import os

from aws import s3
from utils import sql

s3_handler = s3.S3Handler()


# CONVERTS S3 FILE INTO STANDARD CSV
def format_file(bucket, objectKey, log_id="", delimiter=",", columnMap="", lineterminator=""):
    name, _ext = os.path.splitext(objectKey)
    data = s3_handler.s3_to_df(bucket=bucket, object_key=objectKey, delimiter=delimiter)
    s3FileName = f"""{"/".join(name.split("/")[:-1])}/{log_id}_{name.split("/")[-1]}.csv"""
    # s3FileName ='/'.join(name.split('/')[:-2])}{log_id}_{name.split[:-2]}.csv"
    print(s3FileName)
    print("DATA EXTRACTED")
    # print({list(data.columns)[i]:'' for i in range(len(list(data.columns)))})
    # print('-'*50)

    if isinstance(columnMap, dict):
        columnMap = {k.upper(): v.upper() for k, v in columnMap.items()}
        data.columns = [c.upper() for c in data.columns]
        data.rename(columns=columnMap, inplace=True)

    if isinstance(columnMap, list):
        data.columns = columnMap

    data.columns = sql.normalize_col_names(data.columns)
    # print(data.columns)
    print("DATA CONVERTED")

    s3_handler.send_to_s3(data=data, bucket=bucket, s3_file_name=s3FileName)
    print("DATA SENT TO S3")
    # print(data)
    return s3FileName, data.columns.to_list(), data
