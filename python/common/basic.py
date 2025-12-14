import contextlib
import datetime as dt
import ipaddress
import json
import os
import uuid

import numpy as np
import pandas as pd


# TEST
# %% Random Functions
# generates a UUID string
def get_uuid(uuidVer=4, format="str"):
    if uuidVer == 4:
        id = uuid.uuid4()
    if format.lower() == "str":
        return str(id)
    if format.lower() == "hex":
        return id.hex
    return None


# Returns a list of words
def get_list_of_words():
    import requests

    word_site = "https://www.mit.edu/~ecprice/wordlist.10000"
    f = requests.get(word_site)
    return f.text.split("\n")


# generates a list of alphabetic style "column names" ie: [A,B,C ... AA,AB,AC, ... BC,BD,BE]
def ColNum2ColName(n):
    convertString = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    base = 26
    i = n - 1

    if i < base:
        return convertString[i]
    return ColNum2ColName(i // base) + convertString[i % base]


# Flattens a dictionary into a single list where each nested field is concated with its parent node
def flatten_dict(dictObj, key=False):
    outputDict = {}
    for k, v in dictObj.items():
        if key:
            k = f"{key}_{k}"
        if isinstance(v, dict):
            fDict = flatten_dict(v, k)
            for k2, v2 in fDict.items():
                outputDict[k2] = v2
        else:
            outputDict[k] = v
    return outputDict


# sends email with standard python library
def send_email(
    email_sender, username, password, email_body, email_subject, to, cc="", bcc="", files=None
):
    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    import smtplib

    if files is None:
        files = []
    email_to_addrs = cc.split(";") + bcc.split(";") + to.split(";")
    # email_to_addrs= to.split(";")
    msg = MIMEMultipart()

    print(email_to_addrs)
    msg["From"] = email_sender

    msg["To"] = to
    msg["Cc"] = cc
    msg["Bcc"] = bcc
    msg["Subject"] = email_subject
    print(email_body)

    if isinstance(email_body, str):
        msg.attach(MIMEText(email_body, "plain"))

    if isinstance(email_body, dict):
        msg.attach(MIMEText(email_body.get("text"), email_body.get("style", "plain")))

    for filePath in files:
        with open(filePath, "rb") as tmp:
            print(filePath)
            file = filePath.split("/")[-1]
            part = MIMEBase("application", "octet-stream")
            part.set_payload((tmp).read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename= {file}")
            msg.attach(part)

    server = smtplib.SMTP("smtp.office365.com", 587)
    server.ehlo()
    server.starttls()
    server.login(username, password)
    text = msg.as_string()
    server.sendmail(email_sender, email_to_addrs, text)
    server.quit()


# merges a list of img, pdf, or csv files
def merge_files(outputFilePath, filesGenerated, resize=False, delete=True):
    outputFileExt = os.path.splitext(outputFilePath)[1].lower()
    # print('outputFileExt',outputFileExt)

    if outputFileExt.lower() == ".pdf":
        import PyPDF2

        print(outputFilePath)
        mergeFile = PyPDF2.PdfMerger()
        for file_name in filesGenerated:
            # Append PDF files
            mergeFile.append(file_name)
        # Write out the merged PDF file
        mergeFile.write(outputFilePath)
        mergeFile.close()

    elif outputFileExt.lower() == ".csv":
        df = pd.DataFrame()
        for file_name in filesGenerated:
            # print(file_name)
            df = pd.concat(
                [df, pd.read_csv(file_name, dtype=str, low_memory=False)], ignore_index=True
            )
        df.to_csv(outputFilePath, index=False)
        # print(df)

    elif outputFileExt.lower() == ".png":
        # import cv2
        from PIL import Image

        images = {}
        totalHeight = 0
        totalWidth = 0
        maxWidth = 0

        for _i, file_name in enumerate(filesGenerated):
            # print(file_name)
            img = Image.open(file_name)
            dimensions = img.size
            # print('dimensions',dimensions)
            images[totalHeight] = img
            totalWidth = dimensions[0]
            totalHeight += dimensions[1]

            maxWidth = max(maxWidth, totalWidth)
        # print('calc dimensions', maxWidth, totalHeight)
        finalImage = Image.new("RGB", (maxWidth, totalHeight), "white")
        for position, img in images.items():
            # print(position,img)
            finalImage.paste(img, (0, position))
        # print('final dimensions',finalImage.size)
        # finalImage.show()
        finalImage.save(outputFilePath)
    else:
        print("INVALID OUTPUT")

    if delete:
        for file_name in filesGenerated:
            os.remove(file_name)

    return outputFilePath


def print_nested_obj(data, indent=0):
    if indent == 0:
        print("{")

    for key, value in data.items():
        # Print key with appropriate indentation
        # print(key,value, type(value))
        print("\t" * indent + '"' + str(key) + '":', end=" ")

        if isinstance(value, dict):
            # If value is a dictionary, recursively call print_nested_python_dict
            print("{")
            print_nested_obj(value, indent + 1)
            print("\t" * indent + "},")
        elif isinstance(value, list):
            # If value is a list, print each element with indentation
            print("[")
            for item in value:
                if isinstance(item, (dict, list)):
                    print_nested_obj(item, indent + 1)
                else:
                    print("\t" * (indent + 1) + '"' + item + '"' + ",")
            print("\t" * indent + "],")

        elif isinstance(value, type(None)):
            print(str(value) + ",")
        # Check if value is boolean and print accordingly
        elif isinstance(value, bool) or str(value).lower() in ["true", "false"]:
            print(str(value).capitalize() + ",")
        else:
            print('"' + str(value) + '"' + ",")
    if indent == 0:
        print("}")


def get_best_data_type(value):
    # Check if value is dt.datetime
    if isinstance(value, dt.datetime):
        return value
    # Try converting to int

    if isinstance(value, dict):
        return value

    if isinstance(value, list):
        return value

    if value is None or pd.isnull(value):
        return value

    value = str(value)

    # Try converting to bool
    if value.lower() in ["true", "false"]:
        return value.lower() == "true"

    # Try converting to datetime.date
    date_formats = ["%Y-%m-%d", "%Y/%m/%d", "%m-%d-%Y", "%m/%d/%Y", "%d-%m-%Y", "%d/%m/%Y"]
    for fmt in date_formats:
        try:
            return dt.datetime.strptime(value, fmt).date()
        except ValueError:
            pass

    # Try converting to datetime.datetime
    datetime_formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M",
    ]
    for fmt in datetime_formats:
        try:
            return dt.datetime.strptime(value, fmt)
        except ValueError:
            pass

    # Try converting to UUID
    try:
        return uuid.UUID(value)
    except ValueError:
        pass

    try:
        return int(value)
    except ValueError:
        pass

    # Try converting to float
    try:
        return float(value)
    except ValueError:
        pass
    # Try converting to IPv4Address or IPv6Address
    try:
        return ipaddress.ip_address(value)
    except ValueError:
        pass

    # Default to string
    return value


# %% PANDAS DATAFRAME OPERATIONS


# gets least inclusive datatype for a given value
def type_check(val):
    dataTypes = {
        "str": (0, str),
        # 'timeStamp': (1,pd._libs.tslibs.timestamps.Timestamp),
        "timeStamp": (1, "datetime64[ns]"),  # TIMESTAMP WITHOUT TIME ZONE
        "float": (2, float),
        "int": (3, "Int64"),
    }

    try:
        dt.datetime.strptime(val, "%Y-%m-%d")
        return dataTypes["timeStamp"]
    except Exception:
        pass
        # print('ERROR PARSING TYPE',val,e)

    try:
        dt.datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
        return dataTypes["timeStamp"]
    except Exception:
        pass
        # print('ERROR PARSING TYPE',val,e)
    try:
        # if isinstance(val,pd._libs.tslibs.timestamps.Timestamp):
        #     # print(val)
        #     print('is instance')
        #     return dataTypes['timeStamp']

        # if parse(val, fuzzy=True):
        #     print('Parse Date')
        #     return dataTypes['timeStamp']

        containsDecimal = str(val).find(".") >= 0
        isNumber = False

        # print(str(val).count('-')<= 1,str(val).count('.')<= 1)
        if str(val).count("-") <= 1 and str(val).count(".") <= 1:
            isNumber = str(val).replace(".", "").replace("-", "").isdigit()

        # print(val, containsDecimal, isNumber)
        if isNumber:
            if containsDecimal:
                if (
                    len(str(val).split(".")) == 2
                    and str(val).split(".")[0] != ""
                    and str(val).split(".")[1] != ""
                ):
                    return dataTypes["float"]
                return dataTypes["str"]
            return dataTypes["int"]
        return dataTypes["str"]
    except Exception as e:
        print("ERROR PARSING TYPE", val, e)
        return dataTypes["str"]


# gets least inclusive datatype for a provided column via apply function
def getColType(col):
    # print()
    # set col to temp variable and remove null Values
    tempCol = col
    # tempCol = col.replace('', np.nan)
    tempCol = tempCol.dropna()
    tempCol.infer_objects()
    # print(tempCol.info())
    if not tempCol.empty:
        dataTypes = set(tempCol.apply(type_check))
        # print(dataTypes)
        dataTypes = dict(dataTypes)
        # print(col.name, dataTypes)
        dType = dataTypes[min(dataTypes.keys())]
        # print('SET TO DATATYPE:', dType)
        try:
            tempList = set(tempCol.to_list())
            if dType == "Int64":
                tempCol = tempCol.astype(float).astype(dType)
            else:
                tempCol = tempCol.astype(dType)
        except:
            print("INT MESSUP")
            try:
                val = ""
                for _i, v in enumerate(tempList):
                    val = v
                    int(v)
            except Exception as e:
                print(val, e)
    else:
        tempCol = tempCol.astype(str)
    return tempCol.dtype


# Gets best datatype for each column in dataframe and updates column type
def autoConvert(df):
    # normalizing NULL values
    df = df.replace(to_replace="", value=np.nan)
    df = df.replace(to_replace="None", value=np.nan)

    dfColDefs = df.apply(getColType)
    # print(dfColDefs)
    for i in dfColDefs.index:
        # print(i)
        if dfColDefs.loc[i] == "Int64":
            # print('converting int',dfColDefs.loc[i])
            df[i] = df[i].astype(float).astype(dfColDefs.loc[i])
            # df[i] = df[i].astype(float).astype(dfColDefs.loc[i], errors='ignore')
        else:
            df[i] = df[i].astype(dfColDefs.loc[i])
    return df


# gets memory allocation of a dataframe
def dataframe_size_in_mb(df):
    # Get memory usage of each column
    memory_usage_per_column = df.memory_usage(deep=True)

    # Total memory usage in bytes
    total_memory_usage = memory_usage_per_column.sum()

    # Convert bytes to megabytes
    return total_memory_usage / (1024 * 1024)


# Build randomly generated dataframe
def build_rand_df(randRange=100, colNum=10, rowNum=100, columns=None, absNums=True, intOnly=True):
    if columns is None:
        columns = []
    list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    # if columns == []: columns = colList[:colNum]
    columns = [ColNum2ColName(i) for i in range(1, colNum + 1)]
    # for i in range(1,colNum+1):
    #     print(i, ColNum2ColName(i))

    startRange = 0 if absNums else randRange * -1

    if intOnly:
        return pd.DataFrame(
            np.random.randint(startRange, randRange, size=(rowNum, colNum)), columns=columns
        )
    return pd.DataFrame(
        np.random.uniform(startRange, randRange, size=(rowNum, colNum)), columns=columns
    )


# %% Cryptography
def gen_rsa_keys(key_size=2048, format="pem", save_location=False):
    # standard secret name: 'rsaKeys'
    # GENERATES KEYS AND SAVES TO SECRET AND S3

    """
    keys = lambda_utils.gen_rsa_keys(key_size = 2048, region_name = "us-east-1", format = 'ssh', secretID = 'nbp_sftp_key' ,save_location = 's3', client ='NBP')
    print(json.dumps(keys))
    """
    from cryptography.hazmat.primitives import serialization as crypto_serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)

    if format.lower() == "pem":
        private_key = key.private_bytes(
            encoding=crypto_serialization.Encoding.PEM,
            format=crypto_serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=crypto_serialization.NoEncryption(),
        ).decode("utf-8")

        public_key = (
            key.public_key()
            .public_bytes(
                encoding=crypto_serialization.Encoding.PEM,
                format=crypto_serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            .decode("utf-8")
        )

    if format.lower() == "ssh":
        private_key = key.private_bytes(
            crypto_serialization.Encoding.PEM,
            crypto_serialization.PrivateFormat.OpenSSH,
            crypto_serialization.NoEncryption(),
        ).decode("utf-8")

        public_key = (
            key.public_key()
            .public_bytes(
                crypto_serialization.Encoding.OpenSSH, crypto_serialization.PublicFormat.OpenSSH
            )
            .decode("utf-8")
        )

    keys = {"public key": public_key, "private key": private_key}

    if save_location:
        # print(type(save_location))
        if isinstance(save_location, bool):
            # print('TWAS BOOL',type(save_local))
            with open("private_key.pem", "w") as private_key_file:
                private_key_file.write(private_key)

            with open("public_key.txt", "w") as public_key_file:
                public_key_file.write(public_key)

        if isinstance(save_location, str):
            with open(f"{save_location}/private_key.pem", "w") as private_key_file:
                private_key_file.write(private_key)

            with open(f"{save_location}/public_key.txt", "w") as public_key_file:
                public_key_file.write(public_key)

    return keys


def decrypt_data(cypherData, privateKey):
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import padding, serialization
    from cryptography.hazmat.primitives.asymmetric import padding as asymmetric_padding
    from cryptography.hazmat.primitives.ciphers import Cipher
    from cryptography.hazmat.primitives.ciphers.algorithms import AES
    from cryptography.hazmat.primitives.ciphers.modes import CBC
    from cryptography.hazmat.primitives.hashes import SHA256

    for k, v in cypherData.items():
        cypherData[k] = bytes(v, "latin-1")
        # print(cypherData[k])

    # privateKey = bytes(privateKey, 'utf-8')
    # print(privateKey)
    privateKey = serialization.load_pem_private_key(
        privateKey, password=None, backend=default_backend()
    )

    # Decrypt AES key
    oaep_padding = asymmetric_padding.OAEP(
        mgf=asymmetric_padding.MGF1(algorithm=SHA256()), algorithm=SHA256(), label=None
    )
    recovered_key = privateKey.decrypt(cypherData["cipherkey"], oaep_padding)
    # print('recovered_key',recovered_key)
    # Decrypt padded plaintext
    aes_cbc_cipher = Cipher(AES(recovered_key), CBC(cypherData["iv"]))
    recovered_padded_plaintext = aes_cbc_cipher.decryptor().update(cypherData["ciphertext"])

    # Remove padding
    pkcs7_unpadder = padding.PKCS7(AES.block_size).unpadder()
    recovered_data = pkcs7_unpadder.update(recovered_padded_plaintext) + pkcs7_unpadder.finalize()
    data = recovered_data.decode("utf-8")
    with contextlib.suppress(ValueError):
        data = json.loads(data)

    return data


def encrypt_data(data, publicKey):
    # pip install pycrypto
    # https://onboardbase.com/blog/aes-encryption-decryption/
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import padding, serialization
    from cryptography.hazmat.primitives.asymmetric import padding as asymmetric_padding
    from cryptography.hazmat.primitives.ciphers import Cipher
    from cryptography.hazmat.primitives.ciphers.algorithms import AES
    from cryptography.hazmat.primitives.ciphers.modes import CBC
    from cryptography.hazmat.primitives.hashes import SHA256

    # publicKey = bytes(publicKey, 'utf-8')
    # print(publicKey)
    publicKey = serialization.load_pem_public_key(publicKey, backend=default_backend())

    if isinstance(data, dict):
        data = json.dumps(data)
    # print(data)

    data = bytes(data, "utf-8")
    # print(data)
    # Pad the plaintext
    pkcs7_padder = padding.PKCS7(AES.block_size).padder()
    padded_plaintext = pkcs7_padder.update(data) + pkcs7_padder.finalize()
    # print(padded_plaintext)

    # Generate new random AES-256 key
    key = os.urandom(256 // 8)
    # print('key', key)

    # Generate new random 128 IV required for CBC mode
    iv = os.urandom(128 // 8)
    # print(iv)

    # AES CBC Cipher
    aes_cbc_cipher = Cipher(AES(key), CBC(iv))

    # Encrypt padded plaintext
    ciphertext = aes_cbc_cipher.encryptor().update(padded_plaintext)

    # Encrypt AES key
    oaep_padding = asymmetric_padding.OAEP(
        mgf=asymmetric_padding.MGF1(algorithm=SHA256()), algorithm=SHA256(), label=None
    )
    cipherkey = publicKey.encrypt(key, oaep_padding)

    return {
        "iv": str(iv.decode("latin-1")),
        "ciphertext": str(ciphertext.decode("latin-1")),
        "cipherkey": str(cipherkey.decode("latin-1")),
    }


# %% Requests
def make_http_request(
    url=r"http://localhost:8000/", method="GET", headers=None, params=None, data=None, json=None
):
    import requests

    """
    Make an HTTP request using the requests library.

    Args:
        url (str): The URL to send the request to.
        method (str): The HTTP method to use (default is 'GET').
        headers (dict): A dictionary of headers to include in the request (optional).
        params (dict): A dictionary of URL parameters to include in the request (optional).
        data: The body of the request (optional).
        json: A JSON object to send in the body of the request (optional).

    Returns:
        requests.Response: The response object returned by the server.
    """
    try:
        # Make the HTTP request
        return requests.request(method, url, headers=headers, params=params, data=data, json=json)
    except Exception as e:
        print("An error occurred:", e)
        return None


def merge_requirements(source, newFile):
    sourceReqs = {}
    with open(source) as f:
        lines = f.readlines()
        for line in lines:
            if line.strip():
                qualifier = False
                if ";" in line:
                    qualifier = line.strip().split(";")[-1]
                    module = line.strip().split("==")[0].split(";")[0]
                else:
                    module = line.strip().split("==")[0]
                sourceReqs[module] = qualifier
        # sourceReqs = {line.strip().split('==')[0]: "==".join(line.strip().split('==')[1:]) for line in lines}
    # print(sourceReqs)
    # for k, v in sourceReqs.items():
    #     print(k,v)

    updatedReqs = {}
    with open(newFile) as f:
        lines = f.readlines()
        for line in lines:
            if line.strip():
                qualifier = False
                if ";" in line:
                    qualifier = line.strip().split(";")[-1]
                    # print(line.strip().split('=='), line.strip().split(';')[-1], qualifier)

                    module = line.strip().split(";")[0].split("==")[0]
                else:
                    module = line.strip().split("==")[0]
                updatedReqs[module] = qualifier
    # print(updatedReqs)
    # print('-'*50)
    for k, v in updatedReqs.items():
        if k not in sourceReqs:
            sourceReqs[k] = v
            # print(k,v)
    # print(sourceReqs)
    lines = []
    for k, v in sourceReqs.items():
        # print('-'*5)
        # print(k,v)
        if v:
            lines.append(f"{k};{v}\n")
        else:
            lines.append(f"{k}\n")
    # print(lines)
    with open(source, "w") as f:
        f.writelines(lines)


def print_nested_obj(data, indent=0):
    if indent == 0:
        print("{")

    for key, value in data.items():
        # Print key with appropriate indentation
        # print(key,value, type(value))
        print("\t" * indent + '"' + str(key) + '":', end=" ")

        if isinstance(value, dict):
            # If value is a dictionary, recursively call print_nested_python_dict
            print("{")
            print_nested_obj(value, indent + 1)
            print("\t" * indent + "},")
        elif isinstance(value, list):
            # If value is a list, print each element with indentation
            print("[")
            for item in value:
                if isinstance(item, (dict, list)):
                    print_nested_obj(item, indent + 1)
                else:
                    print("\t" * (indent + 1) + '"' + item + '"' + ",")
            print("\t" * indent + "],")

        elif isinstance(value, type(None)):
            print(str(value) + ",")
        # Check if value is boolean and print accordingly
        elif isinstance(value, bool) or str(value).lower() in ["true", "false"]:
            print(str(value).capitalize() + ",")
        else:
            print('"' + str(value) + '"' + ",")
    if indent == 0:
        print("}")
