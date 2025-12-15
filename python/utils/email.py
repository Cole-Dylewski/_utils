import os
from pathlib import Path
import sys

import boto3

# %%
# Environment Flag
env_keys = [key.lower() for key in os.environ]
if "GLUE_PYTHON_VERSION".lower() in env_keys:
    env = "glue"
elif "AWS_LAMBDA_FUNCTION_VERSION".lower() in env_keys:
    env = "lambda"
else:
    env = "local"

# %% [markdown]
# ## Import _utils


# %%
def find_utils():
    """Find _utils path across environments."""
    try:
        current_dir = Path(__file__).resolve()
    except NameError:
        current_dir = Path.cwd()

    for parent in [current_dir, *list(current_dir.parents)]:
        potential_path = parent / "_utils" / "python"
        if potential_path.exists():
            sys.path.insert(0, str(potential_path))
            print(f"Added _utils path: {potential_path}")
            return True
    return False


# %%
if env == "local" and not find_utils():
    print("Warning: _utils path not found!")
# Import _utils
try:
    from aws import aws_lambda as lambda_utils
    from aws import boto3_session, secrets
except ImportError as e:
    print(f"Failed to import _utils: {e}")
    sys.exit(1)


def get_boto3_session():
    """Create a session using _utils locally, use default session in AWS."""
    if env in ["glue", "lambda"]:
        print(f"Running in {env}, using default session.")
        return boto3.Session()
    print("Running locally, using _utils session.")
    return boto3_session.Session()


session = get_boto3_session()

secrets_handler = secrets.SecretHandler(session=session)


def send_email(
    email_body,
    email_subject,
    to,
    cc="",
    bcc="",
    files=None,
    email_sender="",
    email_creds_secret_name="",
):
    from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    import smtplib

    if files is None:
        files = []
    if not email_sender:
        raise ValueError("email_sender parameter is required")

    if not email_creds_secret_name:
        raise ValueError("email_creds_secret_name parameter is required")

    emailSecret = secrets_handler.get_secret(email_creds_secret_name)

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
    elif isinstance(email_body, dict):
        body_content = email_body.get("text", "")
        body_style = email_body.get("style", "plain")  # 'plain' or 'html'
        msg.attach(MIMEText(body_content, body_style))

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
    server.login(emailSecret["emailUsername"], emailSecret["emailPassword"])
    text = msg.as_string()
    server.sendmail(email_sender, email_to_addrs, text)
    server.quit()
