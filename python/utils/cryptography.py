import json
import os
import secrets  # This is the correct module for generating secure tokens

import boto3
from botocore.exceptions import ClientError  # Import ClientError directly from botocore.exceptions
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asymmetric_padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers import algorithms as ciphers_algorithms
from cryptography.hazmat.primitives.ciphers import modes as ciphers_modes
from cryptography.hazmat.primitives.hashes import SHA256

env_keys = [key.lower() for key in os.environ]
if "GLUE_PYTHON_VERSION".lower() in env_keys:
    environment = "glue"
elif "AWS_LAMBDA_FUNCTION_VERSION".lower() in env_keys:
    environment = "lambda"
else:
    environment = "local"


from _utils.aws import s3, secrets

if environment in ["glue", "lambda"]:
    print(f"Running in {environment}, using default session.")
    import boto3

    session = boto3.Session()
else:
    print("Running locally, using _utils session.")
    from _utils.aws import boto3_session

    session = boto3_session.Session()


# Initialize SecretHandler
secret_handler = secrets.SecretHandler(session=session)
s3_handler = s3.S3Handler(session=session)


def encrypt_data(data, secret="rsaKeys"):
    """
    Encrypts data using RSA and AES encryption.
    """
    try:
        public_key_data = secret_handler.get_secret(secret).get("public key")
        if not public_key_data:
            raise ValueError(f"Public key not found in secret: {secret}")

        public_key = serialization.load_pem_public_key(
            public_key_data.encode("utf-8"), backend=default_backend()
        )

        if isinstance(data, dict):
            data = json.dumps(data)
        data = data.encode("utf-8")

        # Pad the plaintext using PKCS7 padding
        padder = padding.PKCS7(ciphers_algorithms.AES.block_size).padder()
        padded_plaintext = padder.update(data) + padder.finalize()

        # Generate AES-256 key and IV
        key = os.urandom(32)  # 256 bits
        iv = os.urandom(16)  # 128 bits

        # AES CBC Cipher
        aes_cbc_cipher = Cipher(
            ciphers_algorithms.AES(key), ciphers_modes.CBC(iv), backend=default_backend()
        )
        encryptor = aes_cbc_cipher.encryptor()
        ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()

        # Encrypt the AES key with RSA public key using OAEP padding
        oaep_padding = asymmetric_padding.OAEP(
            mgf=asymmetric_padding.MGF1(algorithm=SHA256()), algorithm=SHA256(), label=None
        )
        cipherkey = public_key.encrypt(key, oaep_padding)

        # Return encrypted data as a dictionary
        return {
            "iv": iv.decode("latin-1"),
            "ciphertext": ciphertext.decode("latin-1"),
            "cipherkey": cipherkey.decode("latin-1"),
        }

    except (ValueError, TypeError, ClientError) as e:
        print(f"Encryption failed: {e}")
        return None


def decrypt_data(cypher_data, private_key="", secret="rsaKeys"):
    """
    Decrypts data using RSA and AES decryption.
    """
    try:
        for k, v in cypher_data.items():
            cypher_data[k] = v.encode("latin-1")

        if not private_key:
            private_key_data = secret_handler.get_secret(secret).get("private key")
            if not private_key_data:
                raise ValueError(f"Private key not found in secret: {secret}")
            private_key = private_key_data.encode("utf-8")

        private_key = serialization.load_pem_private_key(
            private_key, password=None, backend=default_backend()
        )

        oaep_padding = asymmetric_padding.OAEP(
            mgf=asymmetric_padding.MGF1(algorithm=SHA256()), algorithm=SHA256(), label=None
        )
        recovered_key = private_key.decrypt(cypher_data["cipherkey"], oaep_padding)

        aes_cbc_cipher = Cipher(
            ciphers_algorithms.AES(recovered_key),
            ciphers_modes.CBC(cypher_data["iv"]),
            backend=default_backend(),
        )
        decryptor = aes_cbc_cipher.decryptor()
        recovered_padded_plaintext = (
            decryptor.update(cypher_data["ciphertext"]) + decryptor.finalize()
        )

        unpadder = padding.PKCS7(ciphers_algorithms.AES.block_size).unpadder()
        recovered_data = unpadder.update(recovered_padded_plaintext) + unpadder.finalize()

        data = recovered_data.decode("utf-8")
        try:
            return json.loads(data)
        except ValueError:
            return data

    except (ValueError, TypeError, ClientError) as e:
        print(f"Decryption failed: {e}")
        return None


def gen_rsa_keys(
    key_size=2048,
    secret_name="",
    region_name="us-east-1",
    key_format="pem",
    save_location=False,
    bucket="",
    client="",
):
    """
    Generates RSA keys, saves them in AWS Secrets Manager and optionally to S3.
    """
    try:
        key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)

        # private_key = key.private_bytes(
        #     encoding=serialization.Encoding.PEM,
        #     format=serialization.PrivateFormat.TraditionalOpenSSL,
        #     encryption_algorithm=serialization.NoEncryption()
        # ).decode("utf-8")

        # public_key = key.public_key().public_bytes(
        #     encoding=serialization.Encoding.PEM,
        #     format=serialization.PublicFormat.SubjectPublicKeyInfo
        # ).decode("utf-8")

        if key_format.lower() == "pem":
            private_key = key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            ).decode("utf-8")

            public_key = (
                key.public_key()
                .public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
                .decode("utf-8")
            )

        if key_format.lower() == "ssh":
            private_key = key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.OpenSSH,
                serialization.NoEncryption(),
            ).decode("utf-8")

            public_key = (
                key.public_key()
                .public_bytes(serialization.Encoding.OpenSSH, serialization.PublicFormat.OpenSSH)
                .decode("utf-8")
            )

        keys = {"public key": public_key, "private key": private_key}

        if secret_name:
            if secret_handler.check_secret_exists(secret_name=secret_name):
                secret_handler.update_secret(secret_name=secret_name, updated_secret_value=keys)
            else:
                secret_handler.create_secret(secret_name=secret_name, secret_value=keys)

        if save_location:
            # print(type(save_location))
            if isinstance(save_location, bool):
                # print('TWAS BOOL',type(save_local))
                private_key_file = open("private_key.pem", "w")
                private_key_file.write(private_key)
                private_key_file.close()

                public_key_file = open("public_key.txt", "w")
                public_key_file.write(public_key)
                public_key_file.close()

            if isinstance(save_location, str):
                if save_location.lower() == "s3":
                    s3_handler.send_to_s3(
                        data=private_key,
                        bucket=bucket,
                        s3_file_name=f"keys/{client}/{client}_private_key.pem",
                    )
                    s3_handler.send_to_s3(
                        data=public_key,
                        bucket=bucket,
                        s3_file_name=f"keys/{client}/{client}_public_key.pem",
                    )

        return keys

    except (ClientError, ValueError) as e:
        print(f"Failed to generate RSA keys: {e}")
        return None


def rotate_secret(secret_id):
    """
    Rotates the RSA keys stored in AWS Secrets Manager.
    """
    try:
        gen_rsa_keys(secret_id=secret_id)
        print(f"Successfully rotated secret {secret_id}")

    except Exception as e:
        print(f"Error rotating secret {secret_id}: {e!s}")
        raise


def generate_api_key_secret(secret_id="", region_name="us-east-1"):
    """
    Generates a new API key and secret pair, saves them in AWS Secrets Manager.

    :param secret_id: The secret ID to save the keys in AWS Secrets Manager.
    :param region_name: The AWS region.
    :return: A dictionary with the API key and secret.
    """
    try:
        # Generate API key and secret using the correct secrets module
        api_key = secrets.token_urlsafe(32)  # Secure random key
        api_secret = secrets.token_urlsafe(64)  # Secure random secret

        key_pair = {"api_key": api_key, "api_secret": api_secret}

        # Save the API key and secret to AWS Secrets Manager if secret_id is provided
        if secret_id:
            secrets_handler.update_secret(secret_name=secret_id, updated_secret_value=key_pair)
            print(f"API key/secret pair saved to AWS Secrets Manager under secret: {secret_id}")

        return key_pair

    except (ClientError, ValueError) as e:
        print(f"Failed to generate API key/secret pair: {e}")
        return None
