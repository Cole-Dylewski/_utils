# Designed for use in AWS Lambda, will save reports to /tmp folder
# Example usage:
# tscSecret = lambda_utils.get_secret('tableauCreds')
# with lambda_utils.tableau_client(printVerbose=True, site=fileArgs['args']['site'], username=tscSecret['username'], password=tscSecret['password'], server_url=tscSecret['server_url']) as tsc:
#     files += tsc.generate_report(
#         view_ids=fileArgs['args'].get('view_ids',''),
#         filename=fileName,
#         pdf_params=fileArgs['args'].get('pdf_params',{}),
#         filters=fileArgs['args'].get('filters',[False]),
#         merge=fileArgs['args'].get('merge',False),
#         resize=fileArgs['args'].get('resize',False)
#     )
import os
import urllib
import json
import requests
import pandas as pd
from urllib import parse
from _utils.aws import secrets as aws_secrets
import requests

class tableau_client:
    def __init__(self, username='', password='', server_url='', site='', api_version=3.15, printVerbose=False, tableau_creds_secret_name='', tableau_creds_2025_secret_name=''):
        import sys
        import requests
        
        # Load credentials from secrets if not provided directly
        if not username or not password or not server_url:
            if not tableau_creds_secret_name:
                raise ValueError("tableau_creds_secret_name parameter is required when username, password, or server_url are not provided")
            secret_handler = aws_secrets.SecretHandler()
            tableau_creds = secret_handler.get_secret(tableau_creds_secret_name)
            if not username:
                username = tableau_creds.get('username', '')
            if not password:
                password = tableau_creds.get('password', '')
            if not server_url:
                server_url = tableau_creds.get('server_url', '')
        
        # print('site',site)
        self.server_url = server_url
        self.username = username
        self.password = password
        self.api_version = api_version
        self.printVerbose = printVerbose
        self.site = self.get_site(site = site)
        
        # Set file path prefix depending on the environment (AWS Lambda or local)
        if os.getcwd() == '/var/task':
            self.filePathPrefix = "/tmp"
        else:
            self.filePathPrefix = f"{os.getcwd()}/tmp"
        # print('site',self.site)
    def __enter__(self):
        # self.login()
        return self
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.logout()
        
    # with tableau.tableau_client(printVerbose=True, username=tscSecret['username'], password=tscSecret['password'], server_url=tscSecret['server_url']) as tsc:
    #     print(tsc.get_site().keys())    
    def get_site(self, site=''):
        import requests
        # legacysSite = self.site
        sitesCreds = self.login(getSites=True)
        
        url = f"{self.server_url}/api/{self.api_version}/sites"
        headers = {
            'X-Tableau-Auth': sitesCreds['token'],
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        sites = {k.lower(): v for k, v in json.loads(response.text).get('sites').items()}
        # self.login(site=legacysSite)
        if site:
            for siteInfo in json.loads(response.text).get('sites').get('site'):
                if site.lower().replace(' ', '') == siteInfo['name'].lower().replace(' ', ''):
                    return siteInfo
            return
        else:
            return {siteInfo.get('name').lower(): siteInfo for siteInfo in json.loads(response.text).get('sites').get('site')}

    def get_meta_data(self, subType='all', page_size=100, output='Dataframe', merge=True, project_id='', workbook_id='', view_id='', datasource_id=''):
        import requests
        subTypes = ['project', 'workbook', 'view', 'datasource']
        
        # Handle subType input
        if isinstance(subType, str):
            subType = subType.lower()
            if subType == 'all':
                subType = subTypes
            if subType in subTypes:
                subTypes = [subType]
        elif isinstance(subType, list):
            subType = [sType.lower() for sType in subType]
            subTypes = [sType for sType in subTypes if sType in subType]
        else:
            print('not recognized')
            return
        
        headers = {
            'X-Tableau-Auth': self.credentials['token'],
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        results = {}
        for i, subType in enumerate(subTypes):
            records = []
            page_number = 1  # 1-based pagination
            total_returned = 0
            done = False
        
            while not done:
                url = f"{self.server_url}/api/{self.api_version}/sites/{self.credentials['site']['id']}/{subType}s"
                url += f"/?pageSize={page_size}&pageNumber={page_number}"
                
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    response_json = json.loads(response.text)
                    if response_json.get('pagination', False):
                        total_returned += int(response_json.get('pagination').get('pageSize'))
                        page_number += 1
                        if total_returned >= int(response_json.get('pagination').get('totalAvailable')):
                            done = True
                    else:
                        done = True
                    records += [flatten_dict(record, key=subType) for record in response_json.get(f'{subType}s').get(subType)]
                else:
                    return json.loads(response.text)
        
            results[subType] = pd.DataFrame(records)
        
        # Apply filters if provided
        if project_id and 'project' in subTypes:
            results['project'] = results['project'][results['project']['project_id'] == project_id]
        if workbook_id and 'workbook' in subTypes:
            results['workbook'] = results['workbook'][results['workbook']['workbook_id'] == workbook_id]
        if view_id and 'view' in subTypes:
            results['view'] = results['view'][results['view']['view_id'] == view_id]
        if datasource_id and 'datasource' in subTypes:
            results['datasource'] = results['datasource'][results['datasource']['datasource_id'] == datasource_id]

        # Merge results if required
        if merge:
            keys = list(results.keys())
            for i, key in enumerate(keys):
                if i == 0:
                    results['output'] = results[key]
                else:
                    leftOn = f'{keys[i-1]}_id'
                    rightOn = f'{key}_{keys[i-1]}_id'
                    
                    if key.lower() == 'datasource' and 'project' in subTypes:
                        leftOn = f'project_id'
                        rightOn = f'{key}_project_id'
        
                    results['output'] = results['output'].merge(results[key], left_on=leftOn, right_on=rightOn, how='left')
            
            results = results['output']
            
            if project_id and 'project' in subTypes:
                results = results[results['project_id'] == project_id]
            if workbook_id and 'workbook' in subTypes:
                results = results[results['workbook_id'] == workbook_id]
            if view_id and 'view' in subTypes:
                results = results[results['view_id'] == view_id]
            if datasource_id and 'datasource' in subTypes:
                results = results[results['datasource_id'] == datasource_id]
            
            if output.lower() == 'json':
                results = results.to_dict('records')
        else:
            if output.lower() == 'json':
                results = {k: v.to_dict('records') for k, v in results.items()}
                
        return results

    def download_view(self, outputType, view_id, subType='view', filter=False, pdfparameters=False, pivot=True):
        from urllib import parse   
        import requests
        parameters = []
        df = False
        if outputType.lower() == 'dataframe':
            df = True
            outputType = 'data'
        
        url = f"{self.server_url}/api/{self.api_version}/sites/{self.credentials['site']['id']}/{subType}s/{view_id}/{outputType.lower()}"
        
        if filter:
            for k, v in filter.items():
                if v:
                    parameters.append(f"vf_{parse.quote(str(k), safe='')}={parse.quote(str(v), safe='')}")
        
        if outputType.lower() == 'pdf':
            for k, v in pdfparameters.items():
                if v:
                    parameters.append(f'{parse.quote(k)}={parse.quote(v)}')
        
        if parameters:
            url += f"?{'&'.join(parameters)}"
        if self.printVerbose:
            print('REQUEST URL:', url)   
        
        response = requests.get(url, headers={
            'X-Tableau-Auth': self.credentials['token'],
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        if df:
            import io
            if response.text == '\n':
                return pd.DataFrame()
            else:
                df = pd.read_csv(io.StringIO(response.content.decode()), sep=",")
                if pivot and 'Measure Values' in df.columns.to_list():
                    df['Measure Values'] = [float(str(n).replace('$', '').replace('%', '').replace(',', '')) for n in df['Measure Values'].to_list()]
                    cols = [c for c in df.columns.values if c not in ('Measure Values', 'Measure Names')]
                    df = pd.pivot(df, values='Measure Values', columns='Measure Names', index=cols).reset_index()
                
                return df  
        else:
            return response
    
    def archive_reports(self, bucket, folder, files=[]):
        # Placeholder for archiving reports to a specified bucket and folder
        return
    def get_user(self):
        url = f"{self.server_url}/api/{self.api_version}/sites/{self.credentials['site']['id']}/users"
        response = requests.get(url, headers={
            'X-Tableau-Auth': self.credentials['token'],
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        return response.text
        
    def generate_report(self, view_ids, filename='', subType='view', pdf_params={}, filters=[False], merge=False, resize=False, archive=True):
        page_types = {p.lower(): p for p in ['A3', 'A4', 'A5', 'B5', 'Executive', 'Folio', 'Ledger', 'Legal', 'Letter', 'Note', 'Quarto', 'Tabloid']}
        orientations = {p.lower(): p for p in ['Landscape', 'Portrait']}
        
        pdfparameters = {
            'type': page_types[pdf_params.get('page_type', 'Legal').lower()],
            'orientation': orientations[pdf_params.get('page_orientation', 'Portrait').lower()],
            'maxAge': pdf_params.get('max_age', False),
            'vizHeight': pdf_params.get('vizHeight', False),
            'vizWidth': pdf_params.get('vizWidth', False)
        }

        view_ids = [{'view_id': view_id, 'viewURL': self.get_meta_data(subType=['view'], output='json', view_id=view_id)[0].get('view_viewUrlName', '')} for view_id in view_ids]

        filename = filename or 'report.pdf'
        ext = os.path.splitext(filename)[1].replace('.', '').lower()
        outputType = 'image' if ext == 'png' else 'data' if ext == 'csv' else 'pdf'

        if isinstance(filters, dict):
            filter_df = pd.DataFrame()
            response = self.download_view(outputType='data', view_id=filters['view_id'], subType='view')
            if response.status_code == 200:
                filter_df = pd.read_csv(io.StringIO(response.content.decode()), sep=",")
            if filters.get('sort by', False):
                filter_df = filter_df.sort_values(by=filters['sort by']['columns'], ascending=filters['sort by'].get('ascending', False)).reset_index(drop=True)
            if filters.get('filter', False):
                for filter in filters['filter']:
                    for k, v in filter.items():
                        if isinstance(v, list):
                            filter_df = filter_df[filter_df[k].isin(v)]
                        else:
                            filter_df = filter_df[filter_df[k] == v]
            if filters.get('limit', False):
                filter_df = filter_df.head(filters['limit'])
            if filters.get('drop', False):
                filter_df = filter_df.drop(filters['drop'], axis=1)
            filter_df = filter_df.drop_duplicates().reset_index(drop=True)
            filters = filter_df.to_dict('records')

        filesGenerated = []
        count = 1
        for filter in filters:
            for view_id in view_ids:
                response = self.download_view(outputType=outputType, filter=filter, pdfparameters=pdfparameters, subType=subType, view_id=view_id['view_id'])
                filePath = f"{self.filePathPrefix}/{count} of {len(filters) * len(view_ids)} {view_id['viewURL']}.{ext}"
                count += 1
                filesGenerated.append(filePath)
                with open(filePath, "wb") as f:
                    f.write(response.content)
        
        if merge:
            mergedFilePath = f'{self.filePathPrefix}/{filename}'
            return [mergedFilePath]
        
        return filesGenerated
    
    def login(self, site='', getSites=False):
        print("LOGGING IN")
        url = f"{self.server_url}/api/{self.api_version}/auth/signin"
        contentUrl = '' if getSites else self.site["contentUrl"]
        payload = json.dumps({
            "credentials": {
                "name": self.username,
                "password": self.password,
                "site": {
                    "contentUrl": contentUrl
                }
            }
        })
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        response = requests.post(url, headers=headers, data=payload)
        self.credentials = json.loads(response.text).get('credentials')
        self.status = 'ACTIVE'
        return self.credentials
    
    def logout(self):
        print("LOGGING OUT")
        url = f"{self.server_url}/api/{self.api_version}/auth/signout"
        headers = {
            'X-Tableau-Auth': self.credentials['token'],
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        response = requests.post(url, headers=headers)
        self.status = 'INACTIVE'
        return response.text


class TableauAPIClient:
    def __init__(self, server_url, username, password, api_version, site_name=""):
        self.server_url = server_url
        self.username = username
        self.password = password
        self.api_version = api_version
        self.site_name = site_name
        self.auth_token = None
        self.site_id = None
        # self.authenticate()  # Uses the 1st function

    def authenticate(self):
        """Authenticate to Tableau Server and set the auth token and site ID."""
        temp_auth_payload = {
            "credentials": {
                "name": self.username,
                "password": self.password,
                "site": {"contentUrl": ""}
            }
        }
        temp_auth_headers = {"Content-Type": "application/json", "Accept": "application/json"}
        temp_response = requests.post(f"{self.server_url}/api/{self.api_version}/auth/signin", json=temp_auth_payload, headers=temp_auth_headers)
        temp_response.raise_for_status()
        temp_token = temp_response.json()["credentials"]["token"]

        sites = self.get_all_sites(temp_token)
        site = next((s for s in sites if s["name"] == self.site_name), None)
        if not site:
            raise ValueError(f"Site with name '{self.site_name}' not found.")
        content_url = site["contentUrl"]

        payload = {
            "credentials": {
                "name": self.username,
                "password": self.password,
                "site": {"contentUrl": content_url}
            }
        }
        response = requests.post(f"{self.server_url}/api/{self.api_version}/auth/signin", json=payload, headers=temp_auth_headers)
        response.raise_for_status()
        credentials = response.json()["credentials"]
        self.auth_token = credentials["token"]
        self.site_id = credentials["site"]["id"]

    def authenticate_for_site(self, site_name=''):
        temp_auth_payload = {
            "credentials": {
                "name": self.username,
                "password": self.password,
                "site": {"contentUrl": ""}
            }
        }
        temp_auth_headers = {"Content-Type": "application/json", "Accept": "application/json"}
        temp_response = requests.post(f"{self.server_url}/api/{self.api_version}/auth/signin", json=temp_auth_payload, headers=temp_auth_headers)
        temp_response.raise_for_status()
        temp_token = temp_response.json()["credentials"]["token"]

        sites = self.get_all_sites(temp_token)
        site = next((s for s in sites if s["name"] == site_name), None)

        if not site:
            raise ValueError(f"Site with name '{site_name}' not found.")

        content_url = site["contentUrl"]
        url = f"{self.server_url}/api/{self.api_version}/auth/signin"
        url = urllib.parse.quote(url, safe='/:?=&')
        payload = {
            "credentials": {
                "name": self.username,
                "password": self.password,
                "site": {"contentUrl": content_url}
            }
        }
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        credentials = response.json()["credentials"]
        self.auth_token = credentials["token"]
        self.site_id = credentials["site"]["id"]
        return self.auth_token, self.site_id

    def get_all_sites(self, auth_token):
        """Retrieve all sites on the Tableau Server."""
        url = f"{self.server_url}/api/{self.api_version}/sites"
        url = urllib.parse.quote(url, safe='/:?=&')
        headers = {"X-Tableau-Auth": auth_token, "Accept": "application/json"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()["sites"]["site"]

    def check_user_in_site(self, username):
        """Check if a user exists in a specific site."""
        # username = urllib.parse.quote(username)
        url = f"{self.server_url}/api/{self.api_version}/sites/{self.site_id}/users?filter=name:eq:{username}"
        url = urllib.parse.quote(url, safe='/:?=&')
        headers = {"X-Tableau-Auth": self.auth_token, "Accept": "application/json"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        users = response.json().get("users", {}).get("user", [])
        return users

    def add_user_to_site(self, username, full_name, site_role, email):
        """Add a user to the site."""
        url = f"{self.server_url}/api/{self.api_version}/sites/{self.site_id}/users"
        url = urllib.parse.quote(url, safe='/:?=&')
        headers = {
            "X-Tableau-Auth": self.auth_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "user": {
                "name": username,
                "fullName": full_name,
                "password": "Test4321@",
                "siteRole": site_role,
                "email": email
            }
        }
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 201:
            user_id = response.json().get("user", {}).get("id")
            return user_id
        elif response.status_code == 409:
            print(f"User '{username}' already exists on site.")
            user_id = self.get_user_id(username)
            print(f'user_id - {user_id}')
            return user_id
        else:
            response.raise_for_status()


    def update_user_details(self, user_id, full_name=None, email=None):
        """Update user details."""
        url = f"{self.server_url}/api/{self.api_version}/sites/{self.site_id}/users/{user_id}"
        url = urllib.parse.quote(url, safe='/:?=&')
        headers = {"X-Tableau-Auth": self.auth_token, "Content-Type": "application/json", "Accept": "application/json"}
        payload = {"user": {"fullName": full_name, "email": email}}
        response = requests.put(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.ok

    def get_user_id(self, username):
        """Retrieve a user's ID by username."""
        users = self.check_user_in_site(username)
        return users[0]["id"] if users else None

    def get_group_id_by_name(self, group_name):
        """Retrieve a group's ID by name."""
        url = f"{self.server_url}/api/{self.api_version}/sites/{self.site_id}/groups"
        url = urllib.parse.quote(url, safe='/:?=&')
        headers = {"X-Tableau-Auth": self.auth_token, "Accept": "application/json"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        groups = response.json().get("groups", {}).get("group", [])
        return next((g["id"] for g in groups if g["name"] == group_name), None)
    
    def check_user_access_across_sites(self, 
                                       target_username, 
                                       target_full_name, 
                                       target_password=None, 
                                       check_sites=[]):
        if len(check_sites) == 0:
            auth_token, site_id = self.authenticate_for_site(site_name=self.site)
            sites = self.get_all_sites(auth_token)
            print("Fetching sites...")
        else:
            sites = check_sites 
        
        for site in sites:
            site_name = site if len(check_sites) > 0 else site["name"]
            print(f"Checking access for user '{target_username}' on site '{site_name}'...")
            
            try:
                auth_token, site_id = self.authenticate_for_site(site_name=site_name)
                users = self.check_user_in_site(target_username)
                
                if users:
                    site_role = users[0]['siteRole']
                    print(f"User '{target_username}' has access to site: {site_name} with role: {site_role}")
                else:
                    print(f"User '{target_username}' does not exist or has no site access. Adding user.")
                    site_role = 'Viewer'
                    user_id = self.add_user_to_site(username = target_username, 
                                                    full_name = target_full_name, 
                                                    site_role = site_role, 
                                                    email = target_username)
                    
                    print(f"User '{target_username}' added to site '{site_name}' with user_id '{user_id}'.")
                    
                    self.update_user_details(user_id =user_id, 
                                             full_name = target_full_name, 
                                             email = target_username)
                    print(f'User {target_username} added and updated successfully.')
                    return True
            except requests.exceptions.HTTPError as e:
                print(f"Error checking site '{site_name}': {e}")


    def list_user_groups(self, user_id):
    
        url = f"{self.server_url}/api/{self.api_version}/sites/{self.site_id}/users/{user_id}/groups"
        url = urllib.parse.quote(url, safe='/:?=&')
        headers = { "X-Tableau-Auth": self.auth_token, "Accept": "application/json"}

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        if response.status_code == 200:
            groups = response.json().get("groups", {}).get("group", [])
            return groups
        else:
            print("Failed to get groups for user:", response.json())
            response.raise_for_status()

    def add_user_to_group(self, group_name, user_id):
        """Add a user to a group by name."""
        group_id = self.get_group_id_by_name(group_name)
        if not group_id:
            group_id = self.create_group(group_name)
        url = f"{self.server_url}/api/{self.api_version}/sites/{self.site_id}/groups/{group_id}/users"
        url = urllib.parse.quote(url, safe='/:?=&')
        headers = {"X-Tableau-Auth": self.auth_token, "Content-Type": "application/json", "Accept": "application/json"}
        payload = {"user": {"id": user_id}}
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.ok
    
    def create_group(self, group_name):
        group_name = str(group_name)
        url = f"{self.server_url}/api/{self.api_version}/sites/{self.site_id}/groups"
        url = urllib.parse.quote(url, safe='/:?=&')
        headers = {
            "X-Tableau-Auth": self.auth_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {"group": {"name": group_name}}
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 201:
            group_id = response.json().get("group", {}).get("id")
            print(f"Successfully created group '{group_name}' with ID '{group_id}'.")
            return group_id
        elif response.status_code == 409:
            print(f"Group '{group_name}' already exists.")
            group_id = self.get_group_id_by_name(group_name)
            return group_id
        else:
            print(f"Failed to create group '{group_name}'.")
            return None

    def add_user_to_group_by_id(self, group_name, user_id):
        group_name = str(group_name)
        group_id = self.get_group_id_by_name(group_name)
        if not group_id:
            print(f"Group '{group_name}' not found. Creating the group.")
            group_id = self.create_group(group_name)
            if not group_id:
                print(f"Failed to create group '{group_name}'. Aborting operation.")
                return

        print(f'Adding user to Group {group_name} with group id {group_id}')
        add_url = f"{self.server_url}/api/{self.api_version}/sites/{self.site_id}/groups/{group_id}/users"
        add_url = urllib.parse.quote(add_url, safe='/:?=&')
        headers = {
            "X-Tableau-Auth": self.auth_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {"user": {"id": user_id}}

        response = requests.post(add_url, json=payload, headers=headers)

        if response.status_code == 200:
            print(f"Successfully added user with ID '{user_id}' to group '{group_name}'.")
        elif response.status_code == 404:
            print(f"User with ID '{user_id}' does not exist in '{group_name}'.")    
        elif response.status_code == 409:
            print(f"User with ID '{user_id}' already exists in '{group_name}'.")    
        else:
            print(f"Failed to add user with ID '{user_id}' to group '{group_name}'.")
            
    def remove_user_from_group_by_name(self, group_name, user_id, api_version = None):
        if api_version is None:
            api_version = self.api_version
        group_name = str(group_name)
        group_id = self.get_group_id_by_name(group_name)
        if not group_id:
            print(f"Group '{group_name}' not found.")
            return

        url = f"{self.server_url}/api/{self.api_version}/sites/{self.site_id}/groups/{group_id}/users/{user_id}"

        headers = {
            "X-Tableau-Auth": self.auth_token,
            "Accept": "application/json"
        }

        response = requests.delete(url, headers=headers)

        if response.status_code == 204:
            print(f"Successfully removed user {user_id} from group '{group_name}'.")
        elif response.status_code == 404:
            print(f"User ({user_id}) is not a memeber of the group '{group_name}'. Skipping")
        else:
            print(f"Failed to remove user {user_id} from group '{group_name}'.")
            print(f"Status Code: {response.status_code}, Response: {response.text}")
