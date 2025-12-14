import base64
from datetime import datetime, timedelta, timezone
import json
import logging

from fastapi import HTTPException

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class CognitoHandler:
    """
    CognitoHandler class to manage AWS Cognito interactions such as user authentication and token refresh.
    """

    def __init__(
        self,
        aws_access_key_id=None,
        aws_secret_access_key=None,
        region_name=None,
        session=None,
        cognito_app_client_id=None,
        cognito_userpool_id=None,
        cognito_region=None,
        cognito_creds_secret_name="",
    ):
        logger.info("AWS Cognito Handler initialized")
        # set cognito credentials

        if not cognito_app_client_id:
            if not cognito_creds_secret_name:
                raise ValueError(
                    "cognito_creds_secret_name parameter is required when cognito_app_client_id is not provided"
                )
            from _utils.aws import secrets

            secret_handler = secrets.SecretHandler()
            cognito_creds = secret_handler.get_secret(cognito_creds_secret_name)
            # print('COGNITO CREDS', cognito_creds)
            cognito_app_client_id = cognito_creds["COGNITO_APP_CLIENT_ID"]
            cognito_userpool_id = cognito_creds["COGNITO_USERPOOL_ID"]
            cognito_region = cognito_creds["COGNITO_REGION"]

        # get aws boto3 session
        if session:
            self.session = session
        else:
            from _utils.aws import boto3_session

            self.session = boto3_session.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region_name,
            )

        # self.client_id = os.getenv("COGNITO_APP_CLIENT_ID")
        # self.user_pool_id = os.getenv("COGNITO_USERPOOL_ID")
        # self.region = os.getenv("COGNITO_REGION", "us-east-1")
        # logger.info("AWS Cognito Handler initialized")

        self.client_id = cognito_app_client_id
        self.user_pool_id = cognito_userpool_id
        self.region = cognito_region
        self.cognito_client = self.session.client("cognito-idp", region_name=region_name)
        logger.info("AWS Cognito Session created successfully")

    def authenticate_user(self, username: str, password: str) -> dict:
        """
        Authenticate a user with AWS Cognito using username and password.

        Args:
            username (str): The username of the user.
            password (str): The password of the user.

        Returns:
            dict: A dictionary containing the Cognito user ID and tokens.
        """
        logger.info(f"Authenticating user {username}")
        try:
            # Authenticate user with AWS Cognito
            response = self.cognito_client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={"USERNAME": username, "PASSWORD": password},
            )
            logger.info("Authentication response received")

            challenge_name = response.get("ChallengeName")
            session = response.get("Session")
            if challenge_name and challenge_name == "NEW_PASSWORD_REQUIRED":
                return {
                    "challenge_name": "NEW_PASSWORD_REQUIRED",
                    "session": session,
                    "message": "Please reset your password to continue.",
                }

            # Return the user ID and token data
            auth_result = response.get("AuthenticationResult")
            if auth_result:
                # Get current time in ISO 8601 format
                now = (
                    datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    + " "
                    + datetime.now().astimezone().strftime("%z")
                )

                # Update custom attribute
                self.cognito_client.admin_update_user_attributes(
                    UserPoolId=self.user_pool_id,
                    Username=username,
                    UserAttributes=[{"Name": "custom:last_login_time", "Value": now}],
                )

                # Successful authentication, return the tokens
                return {
                    "challenge_name": "SUCCESS",
                    "access_token": auth_result["AccessToken"],
                    "id_token": auth_result["IdToken"],
                    "refresh_token": auth_result["RefreshToken"],
                    "expires_in": auth_result["ExpiresIn"],
                    "last_login_time": now,
                    "message": "Logged in successfully.",
                }

        except self.cognito_client.exceptions.NotAuthorizedException as e:
            logger.exception(f"Not authorized: {e!s}")
            raise HTTPException(status_code=401, detail="Invalid username or password")
        except self.cognito_client.exceptions.PasswordResetRequiredException as e:
            logger.exception(f"Password reset required: {e!s}")
            raise HTTPException(status_code=401, detail="Password reset required")
        except self.cognito_client.exceptions.UserNotConfirmedException as e:
            logger.exception(f"User is not confirmed: {e!s}")
            raise HTTPException(status_code=403, detail="User is not confirmed")
        except self.cognito_client.exceptions.UserNotFoundException as e:
            logger.exception(f"User not found: {e!s}")
            raise HTTPException(status_code=404, detail="User not found")
        except Exception as e:
            logger.exception(f"Error during authentication: {e!s}")
            raise HTTPException(status_code=500, detail=f"Authentication failed: {e!s}")

    def refresh_user_token(self, refresh_token: str) -> dict:
        """
        Refresh the user's tokens using a refresh token.

        Args:
            refresh_token (str): The refresh token used to generate new tokens.
        Returns:
            dict: A dictionary containing the Cognito user ID and tokens.
        """
        logger.info("Refreshing token for user")
        try:
            response = self.cognito_client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow="REFRESH_TOKEN_AUTH",
                AuthParameters={"REFRESH_TOKEN": refresh_token},
            )
            result = response["AuthenticationResult"]
            # Decode the ID token to extract the Cognito user ID (sub)
            id_token = result["IdToken"]
            # NOTE: Tokens are sensitive - never print them

            return {
                "challenge_name": "SUCCESS",
                "access_token": result["AccessToken"],
                "refresh_token": refresh_token,
                "id_token": id_token,
                "expires_in": result["ExpiresIn"],
                "message": "Token refreshed successfully.",
            }

        except self.cognito_client.exceptions.NotAuthorizedException:
            logger.warning("Invalid refresh token provided")
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        except self.cognito_client.exceptions.UserNotFoundException:
            logger.warning("User not found for refresh token")
            raise HTTPException(status_code=404, detail="User not found")
        except Exception as e:
            logger.exception(f"Error during token refresh: {e!s}")
            raise HTTPException(status_code=500, detail="Token refresh failed")

    def signout_user(self, refresh_token: str):
        """
        Sign out the user by revoking the refresh token.

        Args:
            refresh_token (str): The refresh token of the user that needs to be revoked.
        Returns:
            dict: A message indicating that signout was successful.
        """
        try:
            # Revoke the token using Cognito's revoke token API
            self.cognito_client.revoke_token(Token=refresh_token, ClientId=self.client_id)
            logger.info("Successfully revoked the token.")
            return {"detail": "Signout successful. Token revoked."}

        except Exception as e:
            logger.exception(f"Error during signout: {e!s}")
            raise HTTPException(status_code=500, detail=f"Signout failed: {e!s}")

    def global_signout_user(self, access_token: str):
        """
        Globally sign out the user by invalidating all of their sessions.

        Args:
            access_token (str): The access token of the user that needs to be globally signed out.
        Returns:
            dict: A message indicating that global signout was successful.
        """
        try:
            self.cognito_client.global_sign_out(AccessToken=access_token)
            logger.info("Successfully performed global signout.")
            return {"detail": "Global signout successful."}
        except Exception as e:
            logger.exception(f"Error during global signout: {e!s}")
            raise HTTPException(status_code=500, detail=f"Global signout failed: {e!s}")

    def force_password(self, username: str, new_password: str, session: str) -> dict:
        """
        Respond to the NEW_PASSWORD_REQUIRED challenge by setting a new password.

        Args:
            username (str): The username of the user.
            new_password (str): The new password the user wants to set.
            session (str): The session token from the NEW_PASSWORD_REQUIRED challenge.

        Returns:
            dict: A dictionary containing the tokens if the password reset is successful.
        """
        try:
            # Respond to the NEW_PASSWORD_REQUIRED challenge with the new password
            response = self.cognito_client.respond_to_auth_challenge(
                ClientId=self.client_id,
                ChallengeName="NEW_PASSWORD_REQUIRED",
                ChallengeResponses={
                    "USERNAME": username,
                    "NEW_PASSWORD": new_password,
                },
                Session=session,  # Session from the previous challenge
            )

            # Extract tokens after successfully completing the challenge
            result = response["AuthenticationResult"]
            return {
                "challenge_name": "SUCCESS",
                "access_token": result["AccessToken"],
                "id_token": result["IdToken"],
                "refresh_token": result["RefreshToken"],
                "expires_in": result["ExpiresIn"],
                "message": "Password was reset successfully.",
            }

        except Exception as e:
            logger.exception(f"Error during password reset challenge: {e!s}")
            raise HTTPException(status_code=500, detail="Failed to reset password")

    def initiate_forgot_password(self, username: str) -> dict:
        """
        Initiates the forgot password flow by sending a verification code to the user's email or phone.
        Args:
            username (str): The username or email of the user.
        Returns:
            dict: A message indicating that the reset code was sent.
        """
        try:
            response = self.cognito_client.forgot_password(
                ClientId=self.client_id, Username=username
            )
            return {
                "message": "Password reset code sent. Please check your email or phone.",
                "delivery": response["CodeDeliveryDetails"],
            }
        except self.cognito_client.exceptions.UserNotFoundException:
            raise HTTPException(status_code=404, detail="User not found")
        except Exception as e:
            logger.exception(f"Error initiating password reset: {e!s}")
            raise HTTPException(status_code=500, detail="Failed to initiate password reset")

    def confirm_forgot_password(
        self, username: str, confirmation_code: str, new_password: str
    ) -> dict:
        """
        Confirms the new password using the code sent to the user's email or phone.
        Args:
            username (str): The username or email of the user.
            confirmation_code (str): The code sent to the user’s email or phone.
            new_password (str): The new password the user wants to set.
        Returns:
            dict: A message indicating that the password reset was successful.
        """
        try:
            self.cognito_client.confirm_forgot_password(
                ClientId=self.client_id,
                Username=username,
                ConfirmationCode=confirmation_code,
                Password=new_password,
            )
            return {
                "message": "Password reset successful. You can now log in with your new password."
            }
        except self.cognito_client.exceptions.ExpiredCodeException as e:
            logger.exception(f"The confirmation code has expired: {e!s}")
            raise HTTPException(status_code=401, detail="The confirmation code has expired.")
        except self.cognito_client.exceptions.CodeMismatchException as e:
            logger.exception(f"Invalid confirmation code: {e!s}")
            raise HTTPException(status_code=401, detail="Invalid confirmation code.")
        except self.cognito_client.exceptions.LimitExceededException as e:
            logger.exception(
                f"Too many attempts. Please wait for sometime before making request.: {e!s}"
            )
            raise HTTPException(
                status_code=429,
                detail="Too many attempts. Please wait before making another request.",
            )
        except Exception as e:
            logger.exception(f"Error confirming password reset: {e!s}")
            raise HTTPException(status_code=500, detail="Failed to confirm password reset")

    def change_password(self, access_token: str, old_password: str, new_password: str) -> dict:
        """
        Allows an authenticated user to change their password.

        Args:
            access_token (str): The user's valid access token.
            old_password (str): The current password of the user.
            new_password (str): The new password to set.

        Returns:
            dict: Success message or error details.
        """
        try:
            self.cognito_client.change_password(
                PreviousPassword=old_password,
                ProposedPassword=new_password,
                AccessToken=access_token,
            )

            return {"message": "Password changed successfully"}

        except self.cognito_client.exceptions.NotAuthorizedException:
            raise HTTPException(status_code=401, detail="Incorrect current password")
        except self.cognito_client.exceptions.InvalidPasswordException:
            raise HTTPException(
                status_code=400, detail="New password does not meet security requirements"
            )
        except self.cognito_client.exceptions.LimitExceededException:
            raise HTTPException(status_code=429, detail="Too many requests. Please try again later")
        except Exception as e:
            logger.exception(f"Error changing password: {e!s}")
            raise HTTPException(status_code=500, detail="Failed to change password")

    def manage_user(
        self,
        username: str,
        email: str,
        first_name: str,
        last_name: str,
        password: str,
        role: str | None = None,
        license_level: str | None = None,
        action: str = "CREATE",
    ) -> dict:
        """
        Manage a Cognito user (Create a new user or reset an existing user's password).

        Args:
            username (str): Username for the user.
            email (str): Email address for the user.
            first_name (str): First name of the user.
            last_name (str): Last name of the user.
            password (str): Password to be set for the user.
            role (Optional[str]): Custom role for the user.
            license_level (Optional[str]): License level.
            action (str): "CREATE" (to create a new user) or "RESET" (to reset password).

        Returns:
            dict: Details of the user.
        """
        try:
            if action == "CREATE":
                logger.info(f"Creating new user: {username}")

                # User attributes
                user_attributes = [
                    {"Name": "email", "Value": email},
                    {"Name": "email_verified", "Value": "true"},
                    {"Name": "given_name", "Value": first_name},
                    {"Name": "family_name", "Value": last_name},
                ]

                if role:
                    user_attributes.append({"Name": "custom:user_role", "Value": role})
                if license_level:
                    user_attributes.append({"Name": "custom:license_level", "Value": license_level})

                # Create user with temporary password
                self.cognito_client.admin_create_user(
                    UserPoolId=self.user_pool_id,
                    Username=username,
                    UserAttributes=user_attributes,
                    TemporaryPassword=password,
                    MessageAction="SUPPRESS",  # Prevent Cognito from sending emails
                    ForceAliasCreation=False,
                )

                logger.info(f"User {username} created successfully.")

            elif action == "RESET":
                print(f"Resetting password for user: {username}")

                # Reset password (forces user to change at next login)
                self.cognito_client.admin_set_user_password(
                    UserPoolId=self.user_pool_id,
                    Username=username,
                    Password=password,
                    Permanent=False,  # Forces password reset at login
                )

                logger.info(
                    f"Password reset successfully for user {username}. User must change password at next login."
                )

            else:
                raise HTTPException(
                    status_code=400, detail=f"Invalid action '{action}'. Use 'CREATE' or 'RESET'."
                )

            # Get user creation time and password expiry time
            user_creation_time = datetime.now()
            password_expiry_time = user_creation_time + timedelta(hours=336)

            # Fetch updated user info
            user_info = self.cognito_client.admin_get_user(
                UserPoolId=self.user_pool_id, Username=username
            )

            # Extract the Cognito user ID (sub attribute)
            cognito_user_id = next(
                (attr["Value"] for attr in user_info["UserAttributes"] if attr["Name"] == "sub"),
                None,
            )
            logger.info(
                f"Cognito User ID: {cognito_user_id}, Password Expiry: {password_expiry_time}"
            )

            # Return basic details of the created user
            return {
                "cognito_user_id": cognito_user_id,
                "username": username,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
                "license_level": license_level,
                "status": user_info["UserStatus"],
                "enabled": user_info["Enabled"],
                "created_at": user_creation_time.astimezone(timezone.utc).strftime(
                    "%Y-%m-%d %H:%M:%S.%f"
                )[:-3]
                + " -0000",
                "password_expiry_time": password_expiry_time.astimezone(timezone.utc).strftime(
                    "%Y-%m-%d %H:%M:%S.%f"
                )[:-3]
                + " -0000",
            }

        except self.cognito_client.exceptions.UsernameExistsException:
            logger.exception(f"User creation failed - Username already exists: {username}")
            raise HTTPException(status_code=409, detail="Username already exists")
        except self.cognito_client.exceptions.InvalidPasswordException as e:
            logger.exception(f"User creation failed - Invalid password: {username}, {e!s}")
            raise HTTPException(status_code=400, detail="Invalid password format")
        except Exception as e:
            logger.exception(f"User creation failed for username: {username}, Error: {e!s}")
            raise HTTPException(status_code=500, detail="Failed to process user request")

    def get_user_by_email(self, email: str) -> dict:
        """
        Fetch Cognito user details using the email address.

        Args:
            email (str): The email of the user.

        Returns:
            dict: User details if found, or an error message.
        """
        try:
            # Search for the user in Cognito using email
            response = self.cognito_client.list_users(
                UserPoolId=self.user_pool_id, Filter=f'email = "{email}"'
            )

            if not response["Users"]:
                raise HTTPException(status_code=404, detail="User not found")

            # Extract the username (which could be the email or a different username)
            username = response["Users"][0]["Username"]

            # Get detailed user attributes
            user_info = self.cognito_client.admin_get_user(
                UserPoolId=self.user_pool_id, Username=username
            )

            # Parse user attributes into a dictionary
            user_attributes = {attr["Name"]: attr["Value"] for attr in user_info["UserAttributes"]}

            # Extract the Cognito user ID (sub attribute)
            cognito_user_id = next(
                (attr["Value"] for attr in user_info["UserAttributes"] if attr["Name"] == "sub"),
                None,
            )

            # Transform attribute names to match API-friendly names
            return {
                "cognito_user_id": cognito_user_id,
                "username": user_info["Username"],
                "email": user_attributes.get("email"),
                "first_name": user_attributes.get("given_name"),
                "last_name": user_attributes.get("family_name"),
                "role": user_attributes.get("custom:user_role"),
                "license_level": user_attributes.get("custom:license_level"),
                "status": user_info["UserStatus"],
                "enabled": user_info["Enabled"],
                "created_at": user_info["UserCreateDate"].isoformat(),  # Convert datetime to string
            }

        except self.cognito_client.exceptions.UserNotFoundException:
            raise HTTPException(status_code=404, detail="User not found")
        except self.cognito_client.exceptions.TooManyRequestsException as e:
            logger.exception(
                f"Too many attempts. Please wait before making another request.: {e!s}"
            )
            raise HTTPException(status_code=429, detail="Too many requests")
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error fetching user by email {email}: {e!s}")
            raise HTTPException(status_code=500, detail="Failed to retrieve user details")

    def get_user_info(self, cognito_user_id: str) -> dict:
        """
        Retrieve information about a user from Cognito by Cognito user ID.

        Args:
            cognito_user_id (str): The unique Cognito user ID.

        Returns:
            dict: A dictionary containing user information from Cognito.
        """
        try:
            # Fetch user information from Cognito
            user = self.cognito_client.admin_get_user(
                UserPoolId=self.user_pool_id, Username=cognito_user_id
            )

            # Log and return the user information
            logger.info(f"Successfully retrieved information for Cognito user {cognito_user_id}")
            return {
                "Username": user.get("Username"),
                "Enabled": user.get("Enabled"),
                "UserStatus": user.get("UserStatus"),
                "Attributes": {
                    attr["Name"]: attr["Value"] for attr in user.get("UserAttributes", [])
                },
                "MFAOptions": user.get("MFAOptions", []),
            }
        except self.cognito_client.exceptions.UserNotFoundException as e:
            logger.exception(f"User not found: {e!s}")
            raise HTTPException(status_code=404, detail="User not found")
        except self.cognito_client.exceptions.TooManyRequestsException as e:
            logger.exception(
                f"Too many attempts. Please wait before making another request.: {e!s}"
            )
            raise HTTPException(status_code=429, detail="Too many requests")
        except Exception as e:
            logger.exception(
                f"Failed to retrieve information for Cognito user {cognito_user_id}: {e!s}"
            )
            raise HTTPException(
                status_code=500, detail="Failed to retrieve user information from Cognito"
            )

    def update_user(self, username: str, updates: dict) -> dict:
        """
        Updates the allowed attributes of a Cognito user.

        Args:
            username (str): The username of the user to update.
            updates (dict): A dictionary of attributes to update.

        Returns:
            dict: Confirmation of the update.
        """
        try:
            # Define the allowed attributes
            # Define the mapping of user-friendly keys to Cognito keys
            logger.info(f"Updating cognito User ID: {username!s}")
            attribute_mapping = {
                "first_name": "given_name",
                "last_name": "family_name",
                "role": "custom:user_role",
                "license_level": "custom:license_level",
            }

            # Transform the keys in the updates dictionary
            update_attributes = [
                {"Name": attribute_mapping[key], "Value": value}
                for key, value in updates.items()
                if key in attribute_mapping and value is not None
            ]

            if not update_attributes:
                raise HTTPException(status_code=406, detail="No valid attributes to update")

            # Perform the update
            self.cognito_client.admin_update_user_attributes(
                UserPoolId=self.user_pool_id, Username=username, UserAttributes=update_attributes
            )
            logger.info(f"Updated fields: {updates}")
            return {
                "message": "User attributes updated successfully",
                "updated_attributes": updates,
            }

        except self.cognito_client.exceptions.UserNotFoundException:
            logger.exception(f"User update failed - Username doesn't exists: {username}")
            raise HTTPException(status_code=404, detail="User not found")
        except Exception as e:
            logger.exception(f"Error updating user {username}: {e!s}")
            raise HTTPException(status_code=500, detail="Failed to update user attributes")

    def enable_user(self, cognito_user_id: str) -> None:
        """
        Enable a previously disabled user in Cognito by Cognito user ID.

        Args:
            cognito_user_id (str): The unique Cognito user ID.
        """
        try:
            # Check if the user is already enabled
            user = self.cognito_client.admin_get_user(
                UserPoolId=self.user_pool_id, Username=cognito_user_id
            )

            # If the user is already enabled, return a message
            if user.get("Enabled", False):  # 'Enabled' is True
                logger.info(f"User {cognito_user_id} is already enabled.")
                return {
                    "status": "already_enabled",
                    "message": "User is already enabled",
                }  # Exit the function, as no further action is needed

            # Enable the user if they are currently disabled
            self.cognito_client.admin_enable_user(
                UserPoolId=self.user_pool_id, Username=cognito_user_id
            )
            logger.info(f"Successfully enabled Cognito user {cognito_user_id}")
            return {"status": "enabled", "message": "User has been enabled successfully"}

        except self.cognito_client.exceptions.UserNotFoundException as e:
            logger.exception(f"User not found: {e!s}")
            raise HTTPException(status_code=404, detail="User not found")
        except self.cognito_client.exceptions.TooManyRequestsException as e:
            logger.exception(
                f"Too many attempts. Please wait before making another request.: {e!s}"
            )
            raise HTTPException(status_code=429, detail="Too many requests")
        except Exception as e:
            logger.exception(f"Failed to enable Cognito user {cognito_user_id}: {e!s}")
            raise HTTPException(status_code=500, detail="Failed to enable user in Cognito")

    def disable_user(self, cognito_user_id: str) -> None:
        """
        Disable a user in Cognito by Cognito user ID.

        Args:
            cognito_user_id (str): The unique Cognito user ID.
        """
        try:
            # Check if the user is already disabled
            user = self.cognito_client.admin_get_user(
                UserPoolId=self.user_pool_id, Username=cognito_user_id
            )

            # Look for the 'enabled' status in the response
            if not user.get("Enabled", True):  # If 'Enabled' is False
                logger.info(f"User {cognito_user_id} is already disabled.")
                return {
                    "status": "already_disabled",
                    "message": "User is already disabled",
                }  # Exit the function, as no further action is needed

            # Disable the user if they are not already disabled
            self.cognito_client.admin_disable_user(
                UserPoolId=self.user_pool_id, Username=cognito_user_id
            )
            logger.info(f"Successfully disabled Cognito user {cognito_user_id}")
            return {"status": "disabled", "message": "User has been disabled successfully"}

        except self.cognito_client.exceptions.UserNotFoundException as e:
            logger.exception(f"User not found: {e!s}")
            raise HTTPException(status_code=404, detail="User not found")
        except self.cognito_client.exceptions.TooManyRequestsException as e:
            logger.exception(
                f"Too many attempts. Please wait before making another request.: {e!s}"
            )
            raise HTTPException(status_code=429, detail="Too many requests")
        except Exception as e:
            logger.exception(f"Failed to disable Cognito user {cognito_user_id}: {e!s}")
            raise HTTPException(status_code=500, detail="Failed to disable user in Cognito")

    def delete_user(self, cognito_user_id: str) -> None:
        """
        Delete a user from Cognito by Cognito user ID.

        Args:
            cognito_user_id (str): The unique Cognito user ID.
        """
        try:
            self.cognito_client.admin_delete_user(
                UserPoolId=self.user_pool_id, Username=cognito_user_id
            )
            logger.info(f"Successfully deleted Cognito user {cognito_user_id}")
        except self.cognito_client.exceptions.UserNotFoundException as e:
            logger.exception(f"User not found: {e!s}")
            raise HTTPException(status_code=404, detail="User not found")
        except self.cognito_client.exceptions.TooManyRequestsException as e:
            logger.exception(
                f"Too many attepts. Please wait for sometime before making request.: {e!s}"
            )
            raise HTTPException(status_code=429, detail="Too many requests")
        except Exception as e:
            logger.exception(f"Failed to delete Cognito user {cognito_user_id}: {e!s}")
            raise HTTPException(status_code=500, detail="Failed to delete user from Cognito")

    def _decode_token(self, token: str) -> dict:
        """
        Decode a JWT token without verification (for extracting user info).
        Note: In production, tokens should be verified using proper JWT libraries.

        Args:
            token: JWT token string

        Returns:
            dict: Decoded token payload
        """
        try:
            # Split token into parts
            parts = token.split(".")
            if len(parts) != 3:
                raise ValueError("Invalid token format")

            # Decode the payload (second part)
            payload = parts[1]
            # Add padding if needed
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += "=" * padding

            decoded = base64.urlsafe_b64decode(payload)
            return json.loads(decoded)
        except Exception as e:
            logger.exception(f"Error decoding token: {e!s}")
            raise HTTPException(status_code=400, detail=f"Invalid token format: {e!s}")

    def _get_cognito_user_id(self, decoded_token: dict) -> str:
        """
        Extract Cognito user ID from decoded token.

        Args:
            decoded_token: Decoded JWT token payload

        Returns:
            str: Cognito user ID (sub claim)
        """
        user_id = decoded_token.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=400, detail="Token does not contain user ID (sub claim)"
            )
        return user_id

    # Fix AWS Permission to make this function work
    def admin_global_signout_user(self, access_token: str):
        """
        Invalidates the identity, access, and refresh tokens that Amazon Cognito issued to a user.

        Args:
            access_token (str): The access token of the user that needs to be globally signed out by admin.
        Returns:
            dict: A message indicating that signout was successful by admin.
        """
        try:
            decoded_id_token = self._decode_token(token=access_token)
            cognito_user_id = self._get_cognito_user_id(decoded_id_token)
            logger.info(f"cognito_user_id: {cognito_user_id}")

            response = self.cognito_client.admin_user_global_sign_out(
                UserPoolId=self.user_pool_id, Username=cognito_user_id
            )
            logger.info(f"Response - {response}")
            return {"detail": "Global signout successful by Admin"}
        except Exception as e:
            logger.exception(f"Error during global signout: {e!s}")
            raise HTTPException(status_code=500, detail=f"Global signout failed by Admin: {e!s}")

    def get_user_auth_events_detailed(self, username: str, max_events: int = 10) -> dict:
        """
        Fetches detailed authentication history and profile information for a specified Cognito user.
        Args:
            username (str): The username of the Cognito user.
            max_events (int, optional): The maximum number of recent authentication events to retrieve. Defaults to 10.
        Returns:
            dict: A dictionary containing user profile information (username, email, full name, status, enabled status, creation date)
                  and a list of recent authentication events. Each event includes event type, response, date, IP address, and location.
        Raises:
            HTTPException: If the user is not found (404), rate limit is exceeded (429), or another error occurs (500).
        """
        try:
            user_data = self.cognito_client.admin_get_user(
                UserPoolId=self.user_pool_id, Username=username
            )
            logger.info(f"Fetched user data for {username}: {user_data}")
            user_attrs = {attr["Name"]: attr["Value"] for attr in user_data["UserAttributes"]}
            full_name = (
                f"{user_attrs.get('given_name', '')} {user_attrs.get('family_name', '')}".strip()
            )

            auth_events_response = self.cognito_client.admin_list_user_auth_events(
                UserPoolId=self.user_pool_id, Username=username, MaxResults=max_events
            )

            auth_events = []
            for event in auth_events_response.get("AuthEvents", []):
                event_context = event.get("EventContextData", {})
                event.get("EventRisk", {})

                auth_events.append(
                    {
                        "event_type": event.get("EventType"),
                        "event_response": event.get("EventResponse"),
                        "event_date": event.get("CreationDate").strftime("%Y-%m-%d %H:%M:%S"),
                        "ip": event_context.get("IpAddress"),
                        "location": event_context.get("City") or "Unknown",
                        # "risk": event_risk.get("RiskDecision"),
                        # "risk_level": event_risk.get("RiskLevel"),
                        # "risk_detected": event_risk.get("CompromisedCredentialsDetected")
                    }
                )

            return {
                "username": username,
                "email": user_attrs.get("email"),
                "full_name": full_name,
                "user_status": user_data.get("UserStatus"),
                "enabled": user_data.get("Enabled"),
                "created_at": user_data.get("UserCreateDate").strftime("%Y-%m-%d %H:%M:%S"),
                "auth_events": auth_events,
            }

        except self.cognito_client.exceptions.UserNotFoundException:
            raise HTTPException(status_code=404, detail=f"User '{username}' not found")
        except self.cognito_client.exceptions.TooManyRequestsException:
            raise HTTPException(
                status_code=429, detail="Rate limit exceeded. Please try again later."
            )
        except Exception as e:
            logger.exception(f"Unexpected error for {username}: {e!s}")
            raise HTTPException(status_code=500, detail="Failed to fetch user auth details")

    def get_all_user_auth_events_detailed(self, max_users: int = 100, max_events: int = 5) -> list:
        """
        Retrieves a detailed summary of authentication events for users in the Cognito user pool.
        Args:
            max_users (int, optional): The maximum number of users to retrieve authentication events for. Defaults to 100.
            max_events (int, optional): The maximum number of authentication events to retrieve per user. Defaults to 5.
        Returns:
            list: A list of user authentication event summaries, each containing metadata for a user.
        Notes:
            - If an error occurs while retrieving events for a user, that user is skipped and a warning is logged.
            - The function stops retrieving users once `max_users` is reached.
        """
        summary = []
        paginator = self.cognito_client.get_paginator("list_users")
        count = 0

        for page in paginator.paginate(UserPoolId=self.user_pool_id):
            for user in page.get("Users", []):
                username = user.get("Username")
                try:
                    user_summary = self.get_user_auth_events_detailed(
                        username=username, max_events=max_events
                    )
                    summary.append(user_summary)
                except HTTPException as e:
                    logger.warning(f"Skipping user {username}: {e.detail}")
                    continue
                count += 1
                if count >= max_users:
                    break
            if count >= max_users:
                break

        return summary

    def get_all_users_last_activity(self, max_users: int = 100) -> list:
        """
        Retrieves all Cognito users with their most recent authentication activity timestamp.

        Args:
            max_users (int): Maximum number of users to process.

        Returns:
            list: List of users with last activity timestamp.
        """
        all_user_activity = []
        paginator = self.cognito_client.get_paginator("list_users")
        user_count = 0

        try:
            for page in paginator.paginate(UserPoolId=self.user_pool_id):
                for user in page.get("Users", []):
                    username = user.get("Username")
                    if not username:
                        continue

                    # Get auth events
                    try:
                        user_data = self.cognito_client.admin_get_user(
                            UserPoolId=self.user_pool_id, Username=username
                        )
                        last_modified_time = user_data.get("UserCreateDate")

                        auth_events = self.cognito_client.admin_list_user_auth_events(
                            UserPoolId=self.user_pool_id, Username=username, MaxResults=1
                        )
                        last_event = (
                            auth_events.get("AuthEvents", [])[0]["CreationDate"]
                            if auth_events.get("AuthEvents")
                            else last_modified_time
                        )
                        last_activity = (
                            last_event.strftime("%Y-%m-%d %H:%M:%S.%f") if last_event else None
                        )

                    except self.cognito_client.exceptions.UserNotFoundException:
                        last_activity = None
                    except Exception as e:
                        logger.warning(f"Could not fetch activity for {username}: {e!s}")
                        last_activity = None

                    all_user_activity.append(
                        {
                            "email": next(
                                (
                                    attr["Value"]
                                    for attr in user["Attributes"]
                                    if attr["Name"] == "email"
                                ),
                                None,
                            ),
                            "username": username,
                            "status": user.get("UserStatus"),
                            "enabled": user.get("Enabled"),
                            "last_activity": last_activity,
                        }
                    )

                    user_count += 1
                    if user_count >= max_users:
                        break
                if user_count >= max_users:
                    break

            return all_user_activity

        except Exception as e:
            logger.exception(f"Failed to fetch users' last activity: {e!s}")
            raise HTTPException(
                status_code=500, detail="Failed to retrieve users' activity timestamps."
            )
