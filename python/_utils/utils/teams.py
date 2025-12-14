import json, os

env_keys = [key.lower() for key in os.environ.keys()]
if 'GLUE_PYTHON_VERSION'.lower() in env_keys:
    environment = 'glue'
elif 'AWS_LAMBDA_FUNCTION_VERSION'.lower() in env_keys:
    environment = 'lambda'
else: environment = 'local'

from _utils.utils import sql
from _utils.aws import secrets

if environment in ['glue', 'lambda']:
    print(f"Running in {environment}, using default session.")
    import boto3
    session = boto3.Session()
else:
    print("Running locally, using _utils session.")
    from _utils.aws import boto3_session
    session = boto3_session.Session()


secrets_handler = secrets.SecretHandler(session = session)

def send_teams_notification(channel, users = [], premsg = '', postmsg = '',runQueryType = 'sdk', webhook_secret_name='', directory_schema=''):
    import requests
    if not webhook_secret_name:
        raise ValueError("webhook_secret_name parameter is required")
    webhook = secrets_handler.get_secret(webhook_secret_name)[channel]
    if isinstance(users,list):
        if len(users) > 0:
            users = "','".join([i.lower() for i in users])
        else:
            users  = False
    bodyVals = []
    entityVals = []
    # print(query)
    # print(users)
    if users:
        if not directory_schema:
            raise ValueError("directory_schema parameter is required when users are provided (e.g., 'schema.directory_table')")
        query = f"select * from {directory_schema} where lower(email) in ('{users}');"
        users = sql.run_sql(            
            query = query,#SQL Str: "Select * from table" or "update table set ...." 
            dbname ='dev', #server name
            rds = 'redshift', #'postgreCreds' or 'asyncToolCreds'
            queryType = 'Query'
        )
        for i in range(len(users)):
            bodyVal = f"<at>{users.iloc[i]['first_name']} {users.iloc[i]['last_name']}</at>"
            bodyVals.append(bodyVal)
            entityVals.append({
                  "type": "mention",
                  "text": bodyVal,
                  "mentioned": {
                    "id": users.iloc[i]['email'],
                    "name": users.iloc[i]['first_name']
                  }
                })

    
    print(users)
    print(webhook)
        
    
    body = [
          {
            "type": "TextBlock",
            "size": "Medium",
            "weight": "Bolder",
            "text": "Notification"
          },
        {
            "type": "TextBlock",
            "size": "Medium",
            "wrap": "true",
            "text": f"""{premsg} {', '.join(bodyVals)}"""
          }
        ]

    for line in postmsg.split('\n'):
        body.append({
            "type": "TextBlock",
            "size": "Medium",
            "wrap": "true",
            "text": f"""{line}"""
          })
    
    entities = entityVals
    payload = {
          "type": "message",
          "attachments": [
            {
              "contentType": "application/vnd.microsoft.card.adaptive",
              "content": {
                "type": "AdaptiveCard",
                "body": body,
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "version": "1.0",
                "msteams": {
                  "width": "Full",
                  "entities": entities
                }
              }
            }
          ]
        }
    headers = {
        'Content-Type': 'application/json'
    }
    # print(payload)
    response = requests.post(webhook, headers=headers, data=json.dumps(payload))
