# %%
import json
import os

import pandas as pd
import requests


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


class tableau_client:
    def __init__(
        self, username, password, server_url, site="", api_version=3.15, printVerbose=False
    ):
        global sys
        global requests

        import os
        import sys

        import requests

        # modulenames = set(set(sys.modules) & set(globals()))
        # for name in modulenames:
        #     print(name)
        # print('requests' in set(set(sys.modules) & set(globals())))

        self.server_url = server_url
        self.username = username
        self.password = password

        self.api_version = api_version
        self.printVerbose = printVerbose

        self.site = self.get_site(site)

        if os.getcwd() == "/var/task":
            self.filePathPrefix = "/tmp"
        else:
            self.filePathPrefix = f"{os.getcwd()}\\tmp"

    def __enter__(
        self,
    ):
        self.login()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.logout()

    def get_site(self, site=""):
        # print('SITE',site)
        import requests

        sitesCreds = self.login(getSites=True)
        # print('get site creds?',sitesCreds)

        url = f"{self.server_url}/api/{self.api_version}/sites"

        payload = {}
        headers = {
            "X-Tableau-Auth": sitesCreds["token"],
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        # print('sites',response)
        # print(response.text)
        {k.lower(): v for k, v in json.loads(response.text).get("sites").items()}
        # print(sites.keys())
        # print(sites['site'])
        if site:
            for siteInfo in json.loads(response.text).get("sites").get("site"):
                # print(siteInfo['name'])
                if site.lower().replace(" ", "") == siteInfo["name"].lower().replace(" ", ""):
                    return siteInfo
            return None
        return {
            siteInfo.get("name").lower(): siteInfo
            for siteInfo in json.loads(response.text).get("sites").get("site")
        }

    def get_meta_data(
        self,
        subType="all",  # takes list of different meta types, or a string of a single type,
        page_size=100,  # data page size, if data is too large lower page size, if runtime is too long increase page size, maximum is 1000
        output="Dataframe",  # accepts either DataFrame or JSON
        merge=True,  # if True, will merge all data on heirarchy ids, otherwise will return each subtype as a seperate json or dataframe
        # id values below will filter data on fields
        project_id="",
        workbook_id="",
        view_id="",
        datasource_id="",
    ):
        import json

        import requests

        subTypes = ["project", "workbook", "view", "datasource"]

        if isinstance(subType, str):
            subType = subType.lower()
            if subType == "all":
                subType = subTypes

            if subType in subTypes:
                subTypes = [subType]

        elif isinstance(subType, list):
            subType = [sType.lower() for sType in subType]
            subTypes = [sType for sType in subTypes if sType in subType]

        else:
            print("not recognized")
            return None
        payload = {}
        headers = {
            "X-Tableau-Auth": self.credentials["token"],
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        results = {}
        for i, subType in enumerate(subTypes):
            records = []
            page_number = 1  # 1-based, not zero based
            total_returned = 0
            done = False

            while not (done):
                url = f"{self.server_url}/api/{self.api_version}/sites/{self.credentials['site']['id']}/{subType}s"
                url += f"/?pageSize={page_size}&pageNumber={page_number}"
                # url +="&fields=_all_"
                # print(url)
                response = requests.request("GET", url, headers=headers, data=payload)

                # print(response.status_code)
                if response.status_code == 200:
                    response = json.loads(response.text)

                    # print(response.get('pagination'))
                    # print('*'*100)
                    if response.get("pagination", False):
                        total_returned += int(response.get("pagination").get("pageSize"))
                        page_number += 1
                        # print(total_returned >= int(response.get('pagination').get('totalAvailable')))
                        if total_returned >= int(response.get("pagination").get("totalAvailable")):
                            done = True
                    else:
                        done = True
                    records += [
                        flatten_dict(record, key=subType)
                        for record in response.get(f"{subType}s").get(subType)
                    ]
                else:
                    # print(json.loads(response.text))
                    return json.loads(response.text)

            # print(results[0])

            results[subType] = pd.DataFrame(records)
        if project_id and "project" in subTypes:
            results["project"] = results["project"][results["project"]["project_id"] == project_id]
        if workbook_id and "workbook" in subTypes:
            results["workbook"] = results["workbook"][
                results["workbook"]["workbook_id"] == workbook_id
            ]
        if view_id and "view" in subTypes:
            results["view"] = results["view"][results["view"]["view_id"] == view_id]
        if datasource_id and "datasource" in subTypes:
            results["datasource"] = results["datasource"][
                results["datasource"]["datasource_id"] == datasource_id
            ]

        if merge:
            keys = list(results.keys())

            for i, key in enumerate(keys):
                # print(i, key)
                # print(results[key])
                if i == 0:
                    # print(key)
                    results["output"] = results[key]
                else:
                    if key.lower() != "datasource":
                        leftOn = f"{keys[i - 1]}_id"
                        rightOn = f"{key}_{keys[i - 1]}_id"
                        # print(rightOn)

                    if key.lower() == "datasource" and "project" in subTypes:
                        # print('DATASOURCE AND PROJECT')
                        leftOn = "project_id"
                        rightOn = f"{key}_project_id"
                        # print(rightOn)

                    # print(key, f'{keys[i-1]}_id',rightOn)
                    results["output"] = results["output"].merge(
                        results[key], left_on=leftOn, right_on=rightOn, how="left"
                    )

            results = results["output"]
            if project_id and "project" in subTypes:
                results = results[results["project_id"] == project_id]
            if workbook_id and "workbook" in subTypes:
                results = results[results["workbook_id"] == workbook_id]
            if view_id and "view" in subTypes:
                results = results[results["view_id"] == view_id]
            if datasource_id and "datasource" in subTypes:
                results = results[results["datasource_id"] == datasource_id]

            if output.lower() == "json":
                results = results.to_dict("records")

        elif output.lower() == "json":
            results = {k: v.to_dict("records") for k, v in results.items()}

        return results

    def download_view(
        self,
        outputType,  # data, image, pdf, dataframe
        view_id,
        subType="view",
        filter=False,
        pdfparameters=False,
        pivot=True,
    ):
        from urllib import parse

        import pandas as pd
        import requests

        parameters = []
        df = False
        if outputType.lower() == "dataframe":
            df = True
            outputType = "data"

        url = f"{self.server_url}/api/{self.api_version}/sites/{self.credentials['site']['id']}/{subType}s/{view_id}/{outputType.lower()}"

        if filter:
            # print('FILTER', filter)
            for k, v in filter.items():
                # print(k,v)
                if v:
                    # v = v.replace('/','-')
                    parameters.append(
                        f"vf_{parse.quote(str(k), safe='')}={parse.quote(str(v), safe='')}"
                    )

        # print(parameters)

        if outputType.lower() == "pdf":
            for k, v in pdfparameters.items():
                # print(k,v)
                if v:
                    parameters.append(f"{parse.quote(k)}={parse.quote(v)}")

        # print(url)
        # print(parameters)
        if parameters:
            url += f"?{'&'.join(parameters)}"
        if self.printVerbose:
            print("REQUEST URL:", url)
        response = requests.request(
            "GET",
            url,
            headers={
                "X-Tableau-Auth": self.credentials["token"],
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            data={},
        )
        if df:
            import io

            if response.text == "\n":
                return pd.DataFrame()
            df = pd.read_csv(io.StringIO(response.content.decode()), sep=",")
            if pivot and "Measure Values" in df.columns.to_list():
                # df['Measure Values'] = pd.to_numeric(df['Measure Values'].str.replace('\\,|\\$|\\%', ''))
                df["Measure Values"] = [
                    float(str(n).replace("$", "").replace("%", "").replace(",", ""))
                    for n in df["Measure Values"].to_list()
                ]
                cols = [
                    c for c in df.columns.values if c not in ("Measure Values", "Measure Names")
                ]
                df = pd.pivot(
                    df, values="Measure Values", columns="Measure Names", index=cols
                ).reset_index()

            return df
        return response

    def generate_report(
        self,
        view_ids,
        filename="",
        # outputType = 'pdf',
        subType="view",  # takes list of different meta types, or a string of a single type,
        pdf_params=None,
        filters=None,
        merge=False,
        resize=False,
    ):
        import os

        if filters is None:
            filters = [False]
        if pdf_params is None:
            pdf_params = {}
        page_types = {
            p.lower(): p
            for p in [
                "A3",
                "A4",
                "A5",
                "B5",
                "Executive",
                "Folio",
                "Ledger",
                "Legal",
                "Letter",
                "Note",
                "Quarto",
                "Tabloid",
            ]
        }
        orientations = {p.lower(): p for p in ["Landscape", "Portrait"]}

        pdfparameters = {
            "type": page_types[pdf_params.get("page_type", "Legal").lower()],
            "orientation": orientations[pdf_params.get("page_orientation", "Portrait").lower()],
            "maxAge": pdf_params.get("max_age", False),
            "vizHeight": pdf_params.get("vizHeight", False),
            "vizWidth": pdf_params.get("vizWidth", False),
        }

        if not isinstance(view_ids, list):
            view_ids = [view_ids]

        view_ids = [
            {
                "view_id": view_id,
                "viewURL": self.get_meta_data(subType=["view"], output="json", view_id=view_id)[
                    0
                ].get("view_viewUrlName", ""),
            }
            for view_id in view_ids
        ]

        if self.printVerbose:
            print("VIEW OBJ", view_ids)

        if not filename:
            filename = "radian_report.pdf"
        # print(filename, outputType)
        ext = os.path.splitext(filename)[1].replace(".", "").lower()  # accepts data, pdf, image
        if ext in ["png"]:
            outputType = "image"
        elif ext == "csv":
            outputType = "data"
        else:
            outputType = "pdf"

        if isinstance(filters, dict):
            filters = {k.lower(): v for k, v in filters.items()}
            filterDf = pd.DataFrame()
            import io

            if self.printVerbose:
                print("FILTER ARGS", filters)
            response = self.download_view(
                outputType="data", view_id=filters["view_id"], subType="view"
            )

            if self.printVerbose:
                print("FILTER RESPONSE STATUS CODE", response.status_code)
            if response.status_code == 200:
                filterDf = pd.read_csv(io.StringIO(response.content.decode()), sep=",")
            if self.printVerbose:
                print("initial\n", filterDf)
                print(filterDf.dtypes)
            if filterDf.empty:
                print("NO RESULTS FOUND FOR FILTER ID")
            else:
                if filters.get("sort by"):
                    filterDf = filterDf.sort_values(
                        by=filters["sort by"]["columns"],
                        ascending=filters["sort by"].get("ascending", False),
                    ).reset_index(drop=True)
                if filters.get("filter"):
                    # auto convert dict filters into single element list
                    if isinstance(filters.get("filter"), dict):
                        filters["filter"] = [filters.get("filter")]

                    if isinstance(filters.get("filter"), list):
                        for filter in filters.get("filter"):
                            for k, v in filter.items():
                                if isinstance(v, list):
                                    filterDf = filterDf[filterDf[k].isin(v)]
                                else:
                                    filterDf = filterDf[filterDf[k] == v]
                if filters.get("limit"):
                    filterDf = filterDf.head(filters["limit"])
                if filters.get("drop"):
                    filterDf = filterDf.drop(filters.get("drop"), axis=1)
                filterDf = filterDf.drop_duplicates().reset_index(drop=True)
                if self.printVerbose:
                    print("FINAL\n", filterDf)
                filters = filterDf.to_dict("records")
        count = 1
        filesGenerated = []
        for i, filter in enumerate(filters):
            if self.printVerbose:
                print("FILTER", i, filter)
            for j, view_id in enumerate(view_ids):
                if self.printVerbose:
                    print("VIEW ID", j, view_id)
                response = self.download_view(
                    outputType=outputType,
                    filter=filter,
                    pdfparameters=pdfparameters,
                    subType=subType,
                    view_id=view_id["view_id"],
                )
                if self.printVerbose:
                    print(response)
                filePath = f"{self.filePathPrefix}/{count} of {len(filters) * len(view_ids)} {view_id['viewURL']}.{ext}"
                count += 1
                # print(filePath)
                filesGenerated.append(filePath)
                # print(response.text)

                with open(filePath, "wb") as f:
                    f.write(response.content)
        if merge:
            filesGenerated = merge_files(
                outputFilePath=f"{self.filePathPrefix}/{filename}",
                filesGenerated=filesGenerated,
                resize=resize,
                delete=True,
            )
            return [filesGenerated]

        return filesGenerated

    def login(self, site="", getSites=False):
        url = f"{self.server_url}/api/{self.api_version}/auth/signin"

        "If getSites, then just login with admin account to get site meta data"
        if getSites:
            contentUrl = ""

        elif site:
            if site and isinstance(site, str):
                site = self.get_site(site)

            if site and isinstance(site, dict):
                contentUrl = site["contentUrl"]
        else:
            contentUrl = self.site["contentUrl"]

        payload = json.dumps(
            {
                "credentials": {
                    "name": self.username,
                    "password": self.password,
                    "site": {"contentUrl": contentUrl},
                }
            }
        )
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        response = requests.request("POST", url, headers=headers, data=payload)

        ""
        if not getSites and self.printVerbose:
            print("LOG IN", response)
        self.credentials = json.loads(response.text).get("credentials")
        self.status = "ACTIVE"
        return json.loads(response.text).get("credentials")

    def switch_site(self, site):
        self.logout()
        self.site = self.get_site(site)
        self.login()

    def logout(self):
        url = f"{self.server_url}/api/{self.api_version}/auth/signout"

        payload = {}
        headers = {
            "X-Tableau-Auth": self.credentials["token"],
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        if self.printVerbose:
            print("LOG OUT RESPONSE", response, response.text)
        # print('LOG OUT RESPONSE',response)
        self.status = "INACTIVE"
        return response.text

    def get_attributes(self):
        return self.__dict__

    def print_attributes(self):
        for k, v in self.__dict__.items():
            if isinstance(v, dict):
                print(k)
                for k2, v2 in v.items():
                    print("\t", k2, v2)
            else:
                print(k, v)

    def __str__(self):
        output = {}
        for k, v in self.__dict__.items():
            if k.lower() in ["password"]:
                output[k] = "*" * len(v)
            else:
                output[k] = v
        return json.dumps(output)


# %%
