# %%
def run_sql(
    query,#SQL Str: "Select * from table" or "update table set ...."             
    queryType,
    dbname = 'postgres', #server name  
    host = 'localhost',
    # host = '0.0.0.0',
    port = 5432,
    username = 'postgres',
    password = 'postgres'
    ):
#
    import psycopg2 as PostgreAdapter
    import psycopg2.extras
    import pandas as pd
    creds = f"dbname={dbname} host={host} port={port} user={username} password={password}"
        # print('CREDENTIALS:',creds)
        # baseKeys = '\r'.join(sys.modules.keys())
        # print(baseKeys)
    with psycopg2.connect(creds) as conn:
        with conn.cursor() as cur:
            
            if queryType.lower() in ['operation','procedure']:
                if queryType.lower() == 'procedure':
                    conn.autocommit = True
                    print('AUTOCOMMIT UPDATED',conn.autocommit)
                
                if isinstance(query, list):
                    for stmt in query:
                        cur.execute(stmt)
                    response = 'OPERATIONS COMPLETE'
                else:
                    cur.execute(query)
                    response = 'OPERATION COMPLETE'
                    
                
            elif queryType.lower() == 'query':
                response = pd.read_sql(query,conn)

            else:
                return 'OPERATION TYPE NOT RECOGNIZED'
            conn.commit()
    
    return response

# %% INSERT STMT
# LIKELY UNIFY THIS INTO A DF.to_dict('Records') intermediary pipeline
def dict_to_insert_stmt(log_args, schema, table):

    valuesList = [str(i) for i in log_args.values()]
    columnsList = [str(i) for i in log_args.keys()]
    
    #check each value if it can be converted to a number, store as one if true
    for i, value in enumerate(valuesList):
        if not value.isnumeric():
            valuesList[i] = "'"+value.replace("'",'"')+"'"
        print(i,columnsList[i],':',valuesList[i])
    columns = "(" + ",".join(columnsList)+")"
    values = "VALUES(" + ",".join(valuesList)+")"
    
    insert_stmt = "INSERT INTO {} {} {};".format(f'{schema}.{table}',columns,values)
    print("LOG INSERT STATEMENT \n",insert_stmt)
    return insert_stmt

def df_to_insert_stmt(df, tableName, nullify = [], parseDataTypes=True, strip = False):
    import numpy as np
    for i in nullify:
        df.replace(to_replace=i, value=np.nan, inplace=True)
        #df.fillna(value=np.nan)
    df.dropna(
        axis=0,
        how='all',
        inplace=True
    )
    df.dropna(
        axis=1,
        how='all',
        inplace=True
    )
    
    df.replace(to_replace=[np.nan], value= '' , inplace=True)
    
    # print('DATA\n', df)
    data = df
    cols = '("' + '", "'.join(k.lower() for k in data.keys().to_list()) + '")'
    values = []
    rows = data.values.tolist()
    for row in rows:
        templist = []
        
        for i, value in enumerate(row):
            
            ###Does value contain unicode characters?
            strLen = len(str(value).replace('\n',''))
            utf8strLen = len(str(str(value).replace('\n','').encode('utf-8')))-3
            
            if strip:
                value = str(value).strip()
            if str(value).strip() == '':
                templist.append('NULL')
            
            # Remove unicode characters   
            elif strLen != utf8strLen:
                removeList = [r"\x00"]
                
                try:
                    # print(f"""{value} | {type(value.encode("LATIN1"))}| {value.encode("LATIN1")} | {value.encode("LATIN1").decode("utf-8")} {len(value.encode("LATIN1").decode("utf-8"))}""")
                    outputStr = value.encode("LATIN1")
                    for r in removeList:
                        if str(outputStr)[2:-1] == r:
                            outputStr = b''
                            
                    outputStr = outputStr.decode("utf-8")
                except Exception as e:
                    import re
                    approved = 'abcdefghijklmnopqrstuvwxyz0123456789'.split()
                    outputStr = ''.join([s for s in value if s.lower() in approved])
                    # print(f"""ERROR |{outputStr}|{len(outputStr)}|{e}""")
                    if len(outputStr) == 0:
                        # print('JUST GIVING IT NULL')
                        outputStr = 'NULL'
                    else:
                        print('else')
                        # print(f"""{value} | {type(value.encode("LATIN1"))}| {value.encode("LATIN1")} | {value.encode("LATIN1").decode("utf-8")} {len(value.encode("LATIN1").decode("utf-8"))}""")
                        outputStr = outputStr.encode("LATIN1")
                    # print('except',e)
                finally:
                    templist.append("'" + str(outputStr).replace("'", "''") + "'")
            else:
                value = str(value)
                if parseDataTypes:
                    if (value.count('-')<= 1 and value.count('.')<= 1) and (value.replace('.','').replace('-','').isdigit()):
                        templist.append(value)
                    else:
                        templist.append("'" + value.replace("'", "''") + "'")
                else:
                    templist.append("'" + value.replace("'", "''") + "'")
                    
        insertValue = "(" + ", ".join(templist) + ")"
        # print(insertValue)
        values.append(insertValue)
    values = "\n VALUES \n" + ",\n".join(values)
    return """INSERT INTO {} {} {};""".format(tableName, cols, values)

# %% CREATE STMT
def df_to_createStmt(rds, df, schema, table, batchBool = False):
    schemaTable = f"{schema}.{table}"
    stmtList = [f"DROP TABLE IF EXISTS {schemaTable.upper()};"]
    dataTypeXlat={
        "float64":"FLOAT8",
        "bool":"BOOLEAN",
        "Int64":"BIGINT",
        "timedelta64[ns]":"VARCHAR",
        "int32":"INTEGER",
        "datetime64[ns]":"TIMESTAMP",
        "object":"VARCHAR"
    }
    varCharLengths = [4**i for i in range(1,9)]
    varCharLengths.append(varCharLengths[-1])
    # print(varCharLengths)
    createStmt =f"""CREATE TABLE IF NOT EXISTS {schemaTable.upper()}
("""
    dfColDefs = {}
    colList=[]
    if rds.lower() == 'postgres':
        colList.append("UUID SERIAL") 
    if rds.lower() == 'redshift':
        colList.append("UUID INTEGER not null identity(1,1)")
    
    if batchBool:
        colList.append("BATCH_NAME VARCHAR")
        colList.append("BATCH_STATUS VARCHAR DEFAULT 'ACTIVE'")
        colList.append("BATCH_ID VARCHAR")
        colList.append("USER_NAME VARCHAR")
        colList.append("USER_EMAIL VARCHAR")
        colList.append("LOAD_DATE TIMESTAMP WITHOUT TIME ZONE")
            
    for col in df.columns:
        # print(col)
        dtype = str(df[col].dtype)
        dfColDefs[col] = df[col].dtype
        #UPDATE CHAR REPLACEMENT LOGIC< PROB PUSH TO FUNCTION
        newColName = col
        newColType=''
        # print(dtype)
        if dtype == 'object':            
            maxChar = df[col].str.len().max()
            if str(maxChar) != 'nan':
                # print(col,list(filter(lambda i: i > maxChar, varCharLengths)))
                varCharLim = list(filter(lambda i: i > maxChar, varCharLengths))[1]
                newColType = f"{dataTypeXlat[dtype]}({varCharLim})"
                # print(type(maxChar),maxChar, varCharLim, dtype, dataTypeXlat.keys(), dataTypeXlat[dtype])
            else:
                 newColType = f"{dataTypeXlat[dtype]}"
                
        else:
            newColType =f"{dataTypeXlat[dtype]}"
        newColDef = f'"{newColName}" {newColType}'
        # print(newColDef)
        colList.append(newColDef)
     
    
    # colList.append("UURID INT UNIQUE UNSIGNED NOT NULL AUTO_INCREMENT")
    
    ### ADD COLUMNS FOR ID'ing load  BATCH NAME: CUSTOM FIELD, UUID, USERNAME, EMAIL
        
    # createStmt +={',\n'.join(colList)}
    createStmt +=', \n'.join(colList)
    createStmt +=f' \n);'
    # print(', \n'.join(colList))
    stmtList.append(createStmt)
    
    return stmtList

# %% COPY STMT
def normalize_col_names(cols):
    #CHECK FOR first character as number and duplicates
    acceptableChars = 'abcdefghijklmnopqrstuvwxyz0123456789_'
    # print(acceptableChars)
    newCols=[]
    for col in cols:
        newCol=''
        col = col.replace(' ','_')
        for c in col:
            if c.lower() in acceptableChars:
                newCol+=c
        newCols.append(newCol.upper())
    return newCols

def create_s3_copy_stmt(bucket, key, rds, schema, table, awsSecret, columnMap = '',delimiter = '', region = 'us-east-1'):
    import boto3, os
    import pandas as pd
    s3_client = boto3.client('s3')
    
    obj = s3_client.get_object(Bucket=bucket, Key=key)
    status = obj.get("ResponseMetadata", {}).get("HTTPStatusCode")
    fileSizeMb = obj.get("ContentLength", {}) / (10**6)
    print(status, fileSizeMb)

    tableName = f"{schema}.{table}"
    
    data = pd.DataFrame()
    if status == 200:
        name, ext = os.path.splitext(key)
        
        print("Name = ", name)
        print('EXT = ', ext)
        if delimiter == '' and ext.lower() == '.csv':
            delimiter = ','
            
        if ext.lower() == '.csv':
            data = pd.read_csv(
                obj.get("Body"),
                sep = delimiter,
                nrows = 0
                )
            fileFormat = f"(format csv, header true)"
            if isinstance(columnMap,list):
                data.columns = columnMap
                
            if isinstance(columnMap,dict):
                columnMap = {k.upper():v.upper() for k,v in columnMap.items()}
                data.columns = [c.upper() for c in data.columns]
                data.rename(columns=columnMap, inplace=True) 
                # print(data)               
                
        else:
            if isinstance(columnMap,list):
                data = pd.read_csv(
                    obj.get("Body"), 
                    header = None,
                    names = columnMap,
                    dtype= str, 
                    sep = delimiter, 
                    low_memory=False,
                    nrows = 0
                )
            elif isinstance(columnMap,dict):
                print('DICT?')
                data = pd.read_csv(
                    obj.get("Body"), 
                    dtype= str, 
                    sep = delimiter, 
                    low_memory=False,
                    nrows = 0
                )     
                columnMap = {k.upper():v.upper() for k,v in columnMap.items()}
                data.columns = [c.upper() for c in data.columns]
                data.rename(columns=columnMap, inplace=True) 
                # print(data)
            else:
                print('NO COLUMN MAP')
                data = pd.read_csv(
                    obj.get("Body"), 
                    dtype= str, 
                    sep = delimiter, 
                    low_memory=False,
                    nrows = 0
                )
        # print('DATA HAS BEEN READ')
        headers = normalize_col_names(data.columns.to_list())
        # print('DATABASE CHECK', rds.lower() == 'postgres')

        aws_access_key_id = awsSecret['aws_access_key_id']
        aws_secret_access_key= awsSecret['aws_secret_access_key']
        # print(sts_client.get_session_token())
        
        if rds.lower() == 'postgres':
            # print('headers',headers)
            uploadStmt = f"""SELECT aws_s3.table_import_from_s3(
    '{tableName}',
    '{', '.join(headers)}',
    '(FORMAT CSV, DELIMITER ''{delimiter}'', HEADER TRUE)',
    '{bucket}',
    '{key}',
    '{region}',
    '{aws_access_key_id}',
    '{aws_secret_access_key}'
    );"""
            
        if rds.lower() == 'redshift':
            uploadStmt = f"""COPY {tableName} ({','.join(headers)})
    FROM 's3://{bucket}/{key}' 
    credentials 'aws_access_key_id={aws_access_key_id};aws_secret_access_key={aws_secret_access_key}'
    CSV DELIMITER AS '{delimiter}' 
    BLANKSASNULL
    EMPTYASNULL
    compupdate off
    REGION '{region}'
    ignoreheader 1;"""
            
        return uploadStmt
    else: 
        return 'FILE NOT FOUND'
  
# %% UNLOAD STMT

## REDSHIFT UNLOAD QUERY
def unload_sql(query, bucket, objectKey, awsSecret, delimiter = ','):
    
    aws_access_key_id = awsSecret['aws_access_key_id']
    aws_secret_access_key= awsSecret['aws_secret_access_key']

    # session_token = sts_client.get_session_token()['Credentials']
    # aws_access_key_id = session_token['AccessKeyId']
    # aws_secret_access_key = session_token['SecretAccessKey']
    # aws_access_token = session_token['SessionToken']
   
    unload_qry = f"""UNLOAD('{query}') to 's3://{bucket}/{objectKey}' 
    credentials 'aws_access_key_id= {aws_access_key_id};aws_secret_access_key={aws_secret_access_key}'
    CSV DELIMITER AS '{delimiter}' header parallel off ALLOWOVERWRITE; """

    return unload_qry, bucket, objectKey  
    
## POSTGRES EXPORT QUERY
def export_sql(query, bucket, objectKey, delimiter = ',', region = 'us-east-1'):
   
    s3ExportQuery = f"""SELECT * FROM aws_s3.query_export_to_s3(
    '{query}',
    ('{bucket}','{objectKey}','{region}'),
    ('FORMAT CSV, DELIMITER ''{delimiter}'', HEADER true')
);"""
    
    return s3ExportQuery, bucket, objectKey

## Gets export type based on RDS and returns data to S3 statement
def export_qry_to_s3(rds, query,  bucket, objectKey, delimiter = ',', region  = 'us-east-1', returnS3Info = False):
    
    if rds.lower() ==  'redshift':
        query, bucket, objectKey = unload_sql(query = query, objectKey = objectKey, bucket = bucket, delimiter = delimiter)
        
    if rds.lower() == 'postgres':
        query, bucket, objectKey = export_sql(query = query, objectKey = objectKey,  bucket = bucket, delimiter = delimiter, region = region )

    if returnS3Info:
        return query, bucket, objectKey
        
    else:
        return query