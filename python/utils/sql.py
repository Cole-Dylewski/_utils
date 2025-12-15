# %% Libraries
from collections import Counter
import logging
import os
import time
from typing import Any
import warnings

import asyncpg
import numpy as np
import pandas as pd
import psycopg2 as PostgreAdapter
import psycopg2.extras

env_keys = [key.lower() for key in os.environ]
if "GLUE_PYTHON_VERSION".lower() in env_keys:
    environment = "glue"
elif "AWS_LAMBDA_FUNCTION_VERSION".lower() in env_keys:
    environment = "lambda"
else:
    environment = "local"

from aws import aws_lambda, s3, secrets

if environment in ["glue", "lambda"]:
    print(f"Running in {environment}, using default session.")
    import boto3

    session = boto3.Session()
else:
    print("Running locally, using _utils session.")
    from aws import boto3_session

    session = boto3_session.Session()


s3_handler = s3.S3Handler(session=session)
secret_handler = secrets.SecretHandler(session=session)
lambda_handler = aws_lambda.LambdaHandler(session=session)
warnings.filterwarnings("ignore")
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# %% Misc notes
getAllLockedQueriesOnRedshift = """select a.txn_owner, a.txn_db, a.xid, a.pid, a.txn_start, a.lock_mode, a.relation as table_id,nvl(trim(c."name"),d.relname) as tablename, a.granted,b.pid as blocking_pid ,datediff(s,a.txn_start,getdate())/86400||' days '||datediff(s,a.txn_start,getdate())%86400/3600||' hrs '||datediff(s,a.txn_start,getdate())%3600/60||' mins '||datediff(s,a.txn_start,getdate())%60||' secs' as txn_duration
from svv_transactions a
left join (select pid,relation,granted from pg_locks group by 1,2,3) b
on a.relation=b.relation and a.granted='f' and b.granted='t'
left join (select * from stv_tbl_perm where slice=0) c
on a.relation=c.id
left join pg_class d on a.relation=d.oid
where  a.relation is not null;"""
deleteQuery = """select pg_terminate_backend(pid);"""


def update_handlers(session):
    global s3_handler, secret_handler, lambda_handler
    s3_handler = s3.S3Handler(session=session)
    secret_handler = secrets.SecretHandler(session=session)
    lambda_handler = aws_lambda.LambdaHandler(session=session)


# %% Query Operation
def get_rds_secret(rds):
    if rds.lower() == "postgres":
        return "postgreCreds"
    if rds.lower() == "redshift":
        return "asyncToolCreds"
    return None


def pare_data(data: dict):
    """Utility function to reformat dictionary data."""
    for k, v in data.items():
        data[k] = list(v.values())
    return data


# %% Health Check Ping
async def ping_multiple_databases(databases: dict) -> list:
    """
    Pings a list of databases and returns a list of results indicating success or failure for each.

    Args:
        databases (list): List of dictionaries containing database connection details.
            Each dictionary should have keys: rds, host, port, username, password.

    Returns:
        list: List of dictionaries containing connection results for each database.
    """
    results = {}

    for rds, db in databases.items():
        try:
            print(rds, db)
            secret_handler.get_secret(get_rds_secret(rds))
            # print('secret',secret)
            connection_test = await run_sql_async(
                query="SELECT version();",
                queryType="query",  # Type of query: 'query' or 'execute'
                dbname=db,  # Database name
                rds=rds,
            )
            connection_test = connection_test.to_dict("records")[0]
            print("connection test:", connection_test)
            results[rds] = connection_test
        except Exception as e:
            logger.exception(f"Database connection failed for {db.get('host', 'unknown')}: {e}")
            results.append(
                {"database": db.get("host", "unknown"), "status": "failed", "error": str(e)}
            )

    return results


# %% Asynchronous run_sql_async function
async def run_sql_async(
    query,  # SQL string or list of SQL strings
    queryType,  # Type of query: 'query' or 'execute'
    dbname: str,  # Database name
    secret="",
    rds="",
    host="localhost",
    port=5432,
    username="postgres",
    password="postgres",
    returnType="dataframe",
):
    # Retrieve credentials from AWS Secrets Manager or similar if specified
    if rds or secret:
        if secret:
            rds = "postgres" if secret.lower() == "postgrecreds" else "redshift"
            secret = secret_handler.get_secret(secret)
        elif rds:
            secret = secret_handler.get_secret(get_rds_secret(rds))
        # print("SQL SECRET:",secret)
        creds = {
            "database": dbname,
            "user": secret["username"],
            "password": secret["password"],
            "host": secret["host"],
            "port": secret["port"],
        }
    else:
        creds = {
            "database": dbname,
            "user": username,
            "password": password,
            "host": host,
            "port": port,
        }

    conn = await asyncpg.connect(**creds)
    try:
        start_time = time.time()

        # Start a transaction
        async with conn.transaction():
            if isinstance(query, list):
                total_records_updated = 0
                for q in query:
                    if queryType.lower() == "query":
                        records = await conn.fetch(q)
                        # Count rows if applicable
                        total_records_updated += len(records)
                    elif queryType.lower() in ["operation", "procedure", "execute"]:
                        result = await conn.execute(q)
                        # Parse the number of rows affected from the result string
                        # Example of result format: 'UPDATE 3'
                        if result.startswith(("UPDATE", "DELETE", "INSERT")):
                            affected_rows = int(result.split()[-1])
                            total_records_updated += affected_rows
                    else:
                        raise ValueError("OPERATION TYPE NOT RECOGNIZED")

                runtime = round(time.time() - start_time, 2)
                return {
                    "message": "All queries executed successfully",
                    "affected_rows": total_records_updated,
                    "runtime": runtime,
                }

            # Single query handling (original logic)
            if queryType.lower() in ["operation", "procedure", "execute"]:
                result = await conn.execute(query)
                affected_rows = 0
                if result.startswith(("UPDATE", "DELETE", "INSERT")):
                    affected_rows = int(result.split()[-1])
                runtime = round(time.time() - start_time, 2)
                return {
                    "message": "SQL EXECUTED SUCCESSFULLY",
                    "affected_rows": affected_rows,
                    "runtime": runtime,
                }
            if queryType.lower() == "query":
                records = await conn.fetch(query)
                if returnType.lower() == "dataframe":
                    return pd.DataFrame([dict(record) for record in records])
                return [dict(record) for record in records]
            return "OPERATION TYPE NOT RECOGNIZED"

    except Exception as e:
        logger.exception(f"Error executing SQL: {e}")
        raise

    finally:
        await conn.close()  # Ensure the connection is always closed


# %% Synchronous run_sql function
# Updated Synchronous run_sql function
def run_sql(
    query,  # SQL string or list of SQL strings
    queryType,  # Type of query: 'query' or 'execute'
    dbname: str,  # Database name
    secret="",
    rds="",
    host="localhost",
    port=5432,
    username="postgres",
    password="postgres",
    returnType="dataframe",
):
    # Retrieve credentials from AWS Secrets Manager or similar if specified
    if rds or secret:
        if secret:
            rds = "postgres" if secret.lower() == "postgrecreds" else "redshift"
            secret = secret_handler.get_secret(secret)
        elif rds:
            secret = secret_handler.get_secret(get_rds_secret(rds))

        creds = {
            "dbname": dbname,
            "user": secret["username"],
            "password": secret["password"],
            "host": secret["host"],
            "port": secret["port"],
        }
    else:
        creds = {
            "dbname": dbname,
            "user": username,
            "password": password,
            "host": host,
            "port": port,
        }

    try:
        with PostgreAdapter.connect(**creds) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                start_time = time.time()

                try:
                    # Start a transaction
                    total_records_updated = 0
                    if isinstance(query, list):
                        for q in query:
                            if queryType.lower() == "query":
                                cur.execute(q)
                                # Count rows if applicable
                                total_records_updated += cur.rowcount
                            elif queryType.lower() in ["operation", "procedure", "execute"]:
                                cur.execute(q)
                                # Add the number of affected rows
                                total_records_updated += cur.rowcount
                            else:
                                raise ValueError("OPERATION TYPE NOT RECOGNIZED")

                        runtime = round(time.time() - start_time, 2)
                        conn.commit()  # Commit the transaction if all queries succeed
                        return {
                            "message": "All queries executed successfully",
                            "affected_rows": total_records_updated,
                            "runtime": runtime,
                        }
                    # Single query handling (original logic)
                    if queryType.lower() in ["operation", "procedure", "execute"]:
                        cur.execute(query)
                        affected_rows = cur.rowcount
                        runtime = round(time.time() - start_time, 2)
                        conn.commit()
                        return {
                            "message": "SQL EXECUTED SUCCESSFULLY",
                            "affected_rows": affected_rows,
                            "runtime": runtime,
                        }
                    if queryType.lower() == "query":
                        cur.execute(query)
                        result = cur.fetchall()
                        # print(result)

                        if returnType.lower() == "dataframe":
                            if result:
                                return pd.DataFrame(result)
                            return pd.DataFrame()
                        return result
                    return "OPERATION TYPE NOT RECOGNIZED"

                except Exception as query_error:
                    conn.rollback()  # Rollback the transaction if any query fails
                    logger.exception(f"Error executing SQL, rollback triggered: {query_error}")
                    raise

    except Exception as e:
        logger.exception(f"Error executing SQL: {e}")
        raise


# %% Table Meta Data


def get_table_id(rds, dbname, schema, table, catalog_schema=""):
    if not catalog_schema:
        raise ValueError("catalog_schema parameter is required (e.g., 'schema.table_catalogue')")
    tableIdQuery = f"""select table_id from {catalog_schema}
    where lower(rds) = lower('{rds}')
    and lower(table_catalog) = lower('{dbname}')
    and lower(table_schema) = lower('{schema}')
    and lower(table_name) = lower('{table}');"""
    # print(tableIdQuery)
    response = run_sql(
        query=tableIdQuery,  # SQL Str: "Select * from table" or "update table set ...."
        dbname="dev",  # server name
        secret=get_rds_secret("redshift"),
        queryType="Query",
    )
    print(response)
    if response.empty:
        return ""
    tableId = list(set(response["table_id"].to_list()))
    # print('TABLE ID', tableId)
    if tableId:
        return tableId[0]
    return ""


def retrieve_from_table_id(table_id, catalog_schema=""):
    if not catalog_schema:
        raise ValueError("catalog_schema parameter is required (e.g., 'schema.table_catalogue')")
    query = f"""select
	table_id,
	rds,
	table_catalog,
	table_schema,
	table_name
from
	{catalog_schema}
where table_id = '{table_id}';"""
    table_meta = run_sql(
        query=query,  # SQL Str: "Select * from table" or "update table set ...."
        dbname="dev",  # server name
        queryType="query",
        rds="redshift",  # redshift or postgres
    ).to_dict("Records")[0]

    return (
        table_meta["rds"],
        table_meta["table_catalog"],
        table_meta["table_schema"],
        table_meta["table_name"],
    )


async def get_table_defs(rds: str, dbname: str, schema: str, table: str):
    # SQL query to fetch table definition from the information schema
    table_def_query = f"""
        SELECT
            column_name,
            data_type,
            is_nullable,
            character_maximum_length,
            numeric_precision,
            numeric_scale,
            column_default  -- Used to identify identity columns
        FROM
            information_schema.columns
        WHERE
            table_schema = '{schema}'  -- Specify the schema name
            AND table_name = '{table}' -- Specify the table name
        ORDER BY
            ordinal_position;
    """

    # Run the SQL query asynchronously to get the table definition
    return await run_sql_async(query=table_def_query, queryType="query", dbname=dbname, rds=rds)


# %% Data Validation


def format_sql_value(value):
    """
    Helper function to format SQL values correctly.
    Converts Python types to appropriate SQL representations.
    """
    if value is None:
        return "NULL"  # Use NULL without quotes for SQL
    if isinstance(value, str):
        # return f"'{value.replace("'", "''")}'"  # Enclose strings in single quotes and escape single quotes
        return "'{}'".format(value.replace("'", "''"))

    if isinstance(value, (int, float)):
        return str(value)  # Use numbers directly
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"  # Convert booleans to SQL literals
    raise ValueError(f"Unsupported data type: {type(value)}")


def get_data_type_translation():
    return {
        "float64": "FLOAT8",
        "bool": "BOOLEAN",
        "Int64": "BIGINT",
        "timedelta64[ns]": "VARCHAR",
        "int32": "INTEGER",
        "datetime64[ns]": "TIMESTAMP",
        "object": "VARCHAR",
    }


def resolve_duplicate_cols(cols):
    count = Counter(cols)
    resolved_cols = []
    occurrence = {}

    for col in cols:
        if count[col] > 1:
            if col not in occurrence:
                occurrence[col] = 1
                resolved_cols.append(f"{col}_1")
            else:
                occurrence[col] += 1
                resolved_cols.append(f"{col}_{occurrence[col]}")
        else:
            resolved_cols.append(col)

    return resolved_cols


def normalize_col_names(cols):
    """Normalizes column names by removing non-acceptable characters."""
    cols = [c.lower() for c in cols]
    resolved_cols = resolve_duplicate_cols(cols)
    acceptable_chars = "abcdefghijklmnopqrstuvwxyz0123456789_"
    new_cols = []
    for col in resolved_cols:
        new_col = ""
        col = col.replace(" ", "_")
        for c in col:
            if c.lower() in acceptable_chars:
                new_col += c
        new_cols.append(new_col.lower())
    return new_cols


def sanitize_value(value):
    """Sanitizes an individual value for SQL statements."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "NULL"

    if isinstance(value, str):
        return (
            "'" + value.replace("'", "''") + "'"
        )  # Manually construct the string to avoid f-string issues

    return str(value)


async def validate_data(
    data: dict[str, Any], rds: str, dbname: str, schema: str, table: str, operation: str
):
    """
    Validates the input data against the table definition fetched from the database,
    and skips validation for identity columns.

    Parameters:
    - data: The input data dictionary to be validated.
    - table_meta: Metadata dictionary containing schema and table information.
    - operation: A string indicating the operation type ('INSERT' or 'UPDATE').

    Returns:
    - table_def: The table definition if validation passes, raises ValueError otherwise.
    """

    # Run the SQL query asynchronously to get the table definition
    table_defs = await get_table_defs(rds=rds, dbname=dbname, schema=schema, table=table)

    table_defs = table_defs.to_dict("records")
    # Create a lookup dictionary for column definitions
    column_definitions = {col["column_name"]: col for col in table_defs}

    # Initialize an empty list to collect validation errors
    errors = []

    # Validate each key-value pair in the data against the corresponding column definition
    for column_name, value in data.items():
        # Check if the column exists in the table definition
        if column_name not in column_definitions:
            errors.append(f"Column '{column_name}' does not exist in the table definition.")
            continue

        # Retrieve the column definition
        column_def = column_definitions[column_name]
        data_type = column_def["data_type"]
        is_nullable = column_def["is_nullable"] == "YES"
        max_length = column_def.get("character_maximum_length")
        numeric_precision = column_def.get("numeric_precision")
        numeric_scale = column_def.get("numeric_scale")
        column_default = column_def.get("column_default", "")

        # Skip validation for identity columns
        if column_default and ("nextval" in column_default or "identity" in column_default.lower()):
            # Skip validation for columns with defaults indicating identity behavior
            continue

        # Validate data types
        if data_type in ["integer", "bigint"]:
            if not isinstance(value, int):
                errors.append(
                    f"Column '{column_name}' expects an integer but got {type(value).__name__}."
                )
        elif data_type == "character varying":
            if not isinstance(value, str):
                errors.append(
                    f"Column '{column_name}' expects a string but got {type(value).__name__}."
                )
            elif max_length and len(value) > max_length:
                errors.append(
                    f"Column '{column_name}' value length exceeds maximum of {int(max_length)} characters."
                )
        elif data_type == "boolean":
            if not isinstance(value, bool):
                errors.append(
                    f"Column '{column_name}' expects a boolean but got {type(value).__name__}."
                )
        elif data_type in ["numeric", "decimal"]:
            if not isinstance(value, (int, float)):
                errors.append(
                    f"Column '{column_name}' expects a numeric type but got {type(value).__name__}."
                )
            elif numeric_precision and numeric_scale is not None:
                integer_part = int(numeric_precision - numeric_scale)
                decimal_part = int(numeric_scale)
                value_str = str(value)
                integer_part_value, _, decimal_part_value = value_str.partition(".")
                if len(integer_part_value) > integer_part or len(decimal_part_value) > decimal_part:
                    errors.append(
                        f"Column '{column_name}' value '{value}' exceeds numeric precision {numeric_precision} and scale {numeric_scale}."
                    )

        # Check for NOT NULL constraints; ignore for updates if the value is not provided
        if value is None and not is_nullable:
            if operation.upper() == "INSERT" or (
                operation.upper() == "UPDATE" and column_name in data
            ):
                errors.append(
                    f"Column '{column_name}' cannot be NULL as it is defined as NOT NULL."
                )

    # Check if any required columns are missing for INSERT operation
    if operation.upper() == "INSERT":
        for column_def in table_defs:
            column_name = column_def["column_name"]
            column_default = column_def.get("column_default", "")

            # Skip validation for identity columns
            if column_default and (
                "nextval" in column_default or "identity" in column_default.lower()
            ):
                continue

            if column_name not in data and column_def["is_nullable"] == "NO":
                errors.append(f"Required column '{column_name}' is missing from the data.")

    # Raise a ValueError with collected errors if validation fails
    if errors:
        raise ValueError(f"Validation Errors: {', '.join(errors)}")

    # Return the validated table definition or proceed as needed
    return table_defs


# %% CREATE STMT
def df_to_create_stmt(rds, df, schema, table, batch_bool=False):
    """Generates a CREATE TABLE SQL statement from a DataFrame."""
    schema_table = f"{schema}.{table}".upper()
    stmt_list = [f"DROP TABLE IF EXISTS {schema_table};"]
    data_type_xlat = get_data_type_translation()
    varchar_lengths = [4**i for i in range(1, 9)]
    varchar_lengths.append(varchar_lengths[-1])

    create_stmt = f"CREATE TABLE IF NOT EXISTS {schema_table} ("

    col_defs = []

    if rds.lower() == "postgres":
        col_defs.append("UUID SERIAL")
    elif rds.lower() == "redshift":
        col_defs.append("UUID INTEGER NOT NULL IDENTITY(1,1)")

    if batch_bool:
        col_defs.extend(
            [
                "BATCH_NAME VARCHAR",
                "BATCH_STATUS VARCHAR DEFAULT 'ACTIVE'",
                "BATCH_ID VARCHAR",
                "USER_NAME VARCHAR",
                "USER_EMAIL VARCHAR",
                "LOAD_DATE TIMESTAMP WITHOUT TIME ZONE",
            ]
        )

    for col in df.columns:
        dtype = str(df[col].dtype)
        max_char = df[col].astype(str).str.len().max()
        if dtype == "object" and pd.notna(max_char):
            varchar_limit = next(
                filter(lambda x: x > max_char, varchar_lengths), varchar_lengths[-1]
            )
            col_type = f"VARCHAR({varchar_limit})"
        else:
            col_type = data_type_xlat.get(dtype, "VARCHAR")
        col_defs.append(f'"{col.lower()}" {col_type}')

    create_stmt += ",\n".join(col_defs) + "\n);"
    stmt_list.append(create_stmt)
    logger.info(f"Generated CREATE TABLE statement: {create_stmt}")
    return stmt_list


# %% INSERT STMT
"INSERT STATEMENTS"


def dict_to_insert_stmt(data, schema, table):
    """Generates an INSERT SQL statement from a dictionary."""
    columns = ", ".join(data.keys())
    values = ", ".join(sanitize_value(v) for v in data.values())
    insert_stmt = f"INSERT INTO {schema}.{table} ({columns}) VALUES ({values});"
    logger.info(f"Generated INSERT statement: {insert_stmt}")
    return insert_stmt


def df_to_insert_stmt(df, table_name, nullify=None, parse_data_types=True, strip=False):
    """Generates a bulk INSERT SQL statement from a DataFrame."""
    if nullify is None:
        nullify = []
    df = df.replace(to_replace=nullify, value=np.nan)
    df = df.dropna(axis=0, how="all")
    df = df.dropna(axis=1, how="all")
    # df.fillna('', inplace=True)

    columns = '("' + '", "'.join(df.columns.str.lower()) + '")'
    rows = df.values.tolist()
    values = []

    for row in rows:
        value_list = []
        for value in row:
            if strip:
                value = str(value).strip()
            if parse_data_types and isinstance(value, str):
                if value.replace(".", "", 1).isdigit():
                    value_list.append(value)
                else:
                    value_list.append(sanitize_value(value))
            else:
                value_list.append(sanitize_value(value))
        values.append(f"({', '.join(value_list)})")

    insert_stmt = f"INSERT INTO {table_name} {columns} VALUES \n" + ",\n".join(values) + ";"
    print(insert_stmt)
    logger.info(f"Generated bulk INSERT statement for {len(values)} rows.")
    return insert_stmt


# %% COPY STMT
def create_s3_copy_stmt(
    bucket, key, rds, schema, table, aws_secret, column_map="", delimiter=",", region="us-east-1"
):
    """Generates a COPY statement to import data from S3 into the specified RDS."""

    obj = s3_handler.s3_client.get_object(Bucket=bucket, Key=key)
    status = obj.get("ResponseMetadata", {}).get("HTTPStatusCode")
    if status != 200:
        logger.error(f"Failed to fetch file from S3: {status}")
        return "FILE NOT FOUND"

    file_size_mb = obj.get("ContentLength") / (10**6)
    logger.info(f"Fetched file from S3: {status}, Size: {file_size_mb} MB")

    table_name = f"{schema}.{table}".upper()
    aws_access_key_id = aws_secret["aws_access_key_id"]
    aws_secret_access_key = aws_secret["aws_secret_access_key"]

    data = pd.read_csv(obj.get("Body"), sep=delimiter, nrows=0)
    headers = normalize_col_names(data.columns.to_list())

    if rds.lower() == "postgres":
        upload_stmt = f"""SELECT aws_s3.table_import_from_s3(
            '{table_name}',
            '{", ".join(headers)}',
            '(FORMAT CSV, DELIMITER ''{delimiter}'', HEADER TRUE)',
            '{bucket}',
            '{key}',
            '{region}',
            '{aws_access_key_id}',
            '{aws_secret_access_key}'
        );"""
    elif rds.lower() == "redshift":
        upload_stmt = f"""COPY {table_name} ({", ".join(headers)})
        FROM 's3://{bucket}/{key}'
        credentials 'aws_access_key_id={aws_access_key_id};aws_secret_access_key={aws_secret_access_key}'
        CSV DELIMITER AS '{delimiter}'
        BLANKSASNULL
        EMPTYASNULL
        compupdate off
        REGION '{region}'
        ignoreheader 1;"""
    else:
        logger.error(f"Unsupported RDS type: {rds}")
        return "RDS TYPE NOT SUPPORTED"

    logger.info(f"Generated COPY statement: {upload_stmt}")
    return upload_stmt


# %% UPLOAD STMT


def create_s3_upload_stmt(
    bucket,
    key,
    rds,
    schema,
    table,
    columnMap="",
    delimiter="",
    region="us-east-1",
    aws_redshift_access_key_secret_name="",
):
    obj = s3_client.get_object(Bucket=bucket, Key=key)
    status = obj.get("ResponseMetadata", {}).get("HTTPStatusCode")
    fileSizeMb = obj.get("ContentLength", {}) / (10**6)
    print(status, fileSizeMb)

    tableName = f"{schema}.{table}"

    data = pd.DataFrame()
    if status == 200:
        name, ext = os.path.splitext(key)

        print("Name = ", name)
        print("EXT = ", ext)
        if delimiter == "" and ext.lower() == ".csv":
            delimiter = ","

        if ext.lower() == ".csv":
            data = pd.read_csv(obj.get("Body"), sep=delimiter, nrows=0)
            if isinstance(columnMap, list):
                data.columns = columnMap

            if isinstance(columnMap, dict):
                columnMap = {k.upper(): v.upper() for k, v in columnMap.items()}
                data.columns = [c.upper() for c in data.columns]
                data = data.rename(columns=columnMap)
                # print(data)

        elif isinstance(columnMap, list):
            data = pd.read_csv(
                obj.get("Body"),
                header=None,
                names=columnMap,
                dtype=str,
                sep=delimiter,
                low_memory=False,
                nrows=0,
            )
        elif isinstance(columnMap, dict):
            print("DICT?")
            data = pd.read_csv(obj.get("Body"), dtype=str, sep=delimiter, low_memory=False, nrows=0)
            columnMap = {k.upper(): v.upper() for k, v in columnMap.items()}
            data.columns = [c.upper() for c in data.columns]
            data = data.rename(columns=columnMap)
            # print(data)
        else:
            print("NO COLUMN MAP")
            data = pd.read_csv(obj.get("Body"), dtype=str, sep=delimiter, low_memory=False, nrows=0)
        # print('DATA HAS BEEN READ')
        headers = normalize_col_names(data.columns.to_list())
        # print('DATABASE CHECK', rds.lower() == 'postgres')

        if not aws_redshift_access_key_secret_name:
            raise ValueError("aws_redshift_access_key_secret_name parameter is required")
        awsSecret = secret_handler.get_secret(aws_redshift_access_key_secret_name)
        # print(awsSecret)
        aws_access_key_id = awsSecret["aws_access_key_id"]
        aws_secret_access_key = awsSecret["aws_secret_access_key"]
        # print(sts_client.get_session_token())

        if rds.lower() == "postgres":
            # print('headers',headers)
            uploadStmt = f"""SELECT aws_s3.table_import_from_s3(
    '{tableName}',
    '{", ".join(headers)}',
    '(FORMAT CSV, DELIMITER ''{delimiter}'', HEADER TRUE)',
    '{bucket}',
    '{key}',
    '{region}',
    '{aws_access_key_id}',
    '{aws_secret_access_key}'
    );"""

        if rds.lower() == "redshift":
            uploadStmt = f"""COPY {tableName} ({",".join(headers)})
    FROM 's3://{bucket}/{key}'
    credentials 'aws_access_key_id={aws_access_key_id};aws_secret_access_key={aws_secret_access_key}'
    CSV DELIMITER AS '{delimiter}'
    BLANKSASNULL
    EMPTYASNULL
    compupdate off
    REGION '{region}'
    ignoreheader 1;"""

        return uploadStmt
    return "FILE NOT FOUND"


# %% EXPORT STMT


def unload_sql(query, bucket, object_key, delimiter=",", aws_redshift_access_key_secret_name=""):
    """Generates an UNLOAD SQL statement for Redshift to export data to S3."""

    if not aws_redshift_access_key_secret_name:
        raise ValueError("aws_redshift_access_key_secret_name parameter is required")
    awsSecret = secret_handler.get_secret(aws_redshift_access_key_secret_name)
    aws_access_key_id = awsSecret["aws_access_key_id"]
    aws_secret_access_key = awsSecret["aws_secret_access_key"]

    unload_qry = f"""UNLOAD('{query}') to 's3://{bucket}/{object_key}'
    credentials 'aws_access_key_id= {aws_access_key_id};aws_secret_access_key={aws_secret_access_key}'
    CSV DELIMITER AS '{delimiter}' HEADER PARALLEL OFF ALLOWOVERWRITE;"""

    logger.info(f"Generated UNLOAD statement: {unload_qry}")
    return unload_qry


def export_sql(query, bucket, object_key, delimiter=",", region="us-east-1"):
    """Generates a query export SQL statement for Postgres to export data to S3."""
    s3_export_query = f"""SELECT * FROM aws_s3.query_export_to_s3(
    '{query}',
    ('{bucket}', '{object_key}', '{region}'),
    ('FORMAT CSV, DELIMITER ''{delimiter}'', HEADER TRUE')
    );"""

    logger.info(f"Generated EXPORT statement: {s3_export_query}")
    return s3_export_query


def export_qry_to_s3(
    rds, query, bucket, object_key, delimiter=",", region="us-east-1", return_s3_info=False
):
    """Determines and returns the appropriate export query to S3 based on RDS type."""
    if rds.lower() == "redshift":
        export_query = unload_sql(query, bucket, object_key, delimiter=delimiter)
    elif rds.lower() == "postgres":
        export_query = export_sql(query, bucket, object_key, delimiter=delimiter, region=region)
    else:
        logger.error(f"Unsupported RDS type: {rds}")
        return "RDS TYPE NOT SUPPORTED"

    if return_s3_info:
        return export_query, bucket, object_key
    return export_query


# %% Data Transfer


def migrate_data(
    sourceRDS,
    sourceDbName,
    sourceQuery,
    targetRDS,
    targetDbName,
    targetSchema,
    targetTable,
    requestType,
    payload=None,
    runType="sdk",
    qualifier="",
    formatFile=False,
):
    if payload is None:
        payload = {}
    if not qualifier:
        raise ValueError("qualifier parameter is required")

    # EXPORT THE DATA TO S3
    fileName = (
        f"{sourceRDS}.{sourceDbName} to {targetRDS}.{targetDbName} {targetSchema}.{targetTable}.csv"
    )

    # Extract the data to a CSV
    s3ExportQuery, bucket, objectKey = export_qry_to_s3(
        rds=sourceRDS, query=sourceQuery, fileName=fileName, returnS3Info=True
    )
    print("MIGRATE DATA EXPORT DATA")
    print(s3ExportQuery.replace("\n", "\r"), "|", bucket, "|", objectKey)
    # response = runQuery(query = s3ExportQuery, dbname = sourceDbName, secret = secret , queryType = 'operation')
    # response = send_to_dbconn(payload = payload, query = s3ExportQuery, secret = secret, dbname  = sourceDbName, InvocationType = 'RequestResponse' ,queryType='Operation', printResponse = False)
    response = run_sql(
        query=s3ExportQuery,  # SQL Str: "Select * from table" or "update table set ...."
        dbname=sourceDbName,  # server name
        queryType="operation",
        rds=sourceRDS,  # redshift or postgres
    )
    # print(s3ExportQuery.replace('\n','\r'))
    print("EXPORT RESPONSE:", response)

    # LOAD DATA TO DATABASE
    # response = send_to_s3DBOps(
    #     payload = payload,
    #     requestType = requestType,
    #     bucket = bucket,
    #     key = objectKey,
    #     rds= targetRDS,
    #     database = targetDbName,
    #     schema = targetSchema,
    #     table = targetTable,
    #     invocationType = 'Event',
    #     formatFile = formatFile)
    # print('s3DBOps Response:', response)

    return s3ExportQuery, bucket, objectKey


def s3_to_rds(
    bucket, key, dbname, rds, schema, table, delimiter="", columnMap="", lineterminator=""
):
    get_rds_secret(rds)
    uploadStmt = create_s3_copy_stmt(
        bucket, key, rds, schema, table, columnMap=columnMap, delimiter=delimiter
    )
    print("UPLOADING DATA", uploadStmt.replace("\n", "\r"))
    response = run_sql(
        query=uploadStmt,  # SQL Str: "Select * from table" or "update table set ...."
        dbname=dbname,  # server name
        rds=rds,
        queryType="Operation",
    )
    print("UPLOAD RESPONSE", response)


def df_load_in_chunks(
    df: pd.DataFrame, rds: str, dbname: str, schema: str, table_name: str, chunk_size: int = 1000
):
    print("LOADING DATA")
    total_rows = len(df)
    for start in range(0, total_rows, chunk_size):
        end = min(start + chunk_size, total_rows)
        print(f"Uploading records {start} to {end - 1}")
        insert_stmt = df_to_insert_stmt(df=df.iloc[start:end], table_name=f"{schema}.{table_name}")
        # print(insert_stmt)
        response = run_sql(
            query=insert_stmt,  # SQL Str: "Select * from table" or "update table set ...."
            dbname=dbname,  # server name
            rds=rds,  #'postgreCreds' or 'asyncToolCreds'
            queryType="operation",  # 'query' or 'operation'
        )
        print(f"LOADING RECORDS {start} - {end - 1}", response)


def ping_db_server(
    rds: str = "",
    host: str = "localhost",
    port: int = 5432,
    username: str = "postgres",
    password: str = "postgres",
):
    """
    Pings the PostgreSQL or Redshift server without selecting a specific database.

    Args:
        rds (str, optional): RDS type ('postgres' or 'redshift'). Defaults to ''.
        host (str, optional): Database server host. Defaults to 'localhost'.
        port (int, optional): Database server port. Defaults to 5432.
        username (str, optional): Database username. Defaults to 'postgres'.
        password (str, optional): Database password. Defaults to 'postgres'.

    Returns:
        bool: True if the server connection is successful, False otherwise.
    """
    try:
        # Retrieve credentials from AWS Secrets Manager if using RDS
        if rds:
            secret = secret_handler.get_secret(get_rds_secret(rds))
            creds = {
                "dbname": "postgres",  # Default database name
                "user": secret["username"],
                "password": secret["password"],
                "host": secret["host"],
                "port": secret["port"],
            }
        else:
            creds = {
                "dbname": "postgres",  # Use a generic database like "postgres"
                "user": username,
                "password": password,
                "host": host,
                "port": port,
            }

        # Connect to the database server
        with PostgreAdapter.connect(**creds) as conn, conn.cursor() as cur:
            cur.execute("SELECT version();")  # Check server version
            version = cur.fetchone()
            logger.info(f"Database server is online: {version[0]}")
            return True

    except Exception as e:
        logger.exception(f"Database server connection failed: {e}")
        return False


# CLI functionality
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="SQL utility CLI - Run SQL queries and operations")
    parser.add_argument("query", help="SQL query to execute")
    parser.add_argument(
        "--type",
        "-t",
        choices=["query", "execute"],
        default="query",
        help="Query type: query or execute",
    )
    parser.add_argument("--dbname", "-d", required=True, help="Database name")
    parser.add_argument("--rds", help="RDS type (postgres, redshift)")
    parser.add_argument("--secret", "-s", help="AWS Secrets Manager secret name")
    parser.add_argument("--host", default="localhost", help="Database host")
    parser.add_argument("--port", type=int, default=5432, help="Database port")
    parser.add_argument("--username", "-u", help="Database username")
    parser.add_argument("--password", "-p", help="Database password")
    parser.add_argument(
        "--return-type",
        choices=["dataframe", "dict", "list"],
        default="dataframe",
        help="Return type",
    )
    parser.add_argument("--output", "-o", help="Output file (JSON or CSV)")
    parser.add_argument("--format", choices=["json", "csv"], default="json", help="Output format")

    args = parser.parse_args()

    try:
        result = run_sql(
            query=args.query,
            queryType=args.type,
            dbname=args.dbname,
            secret=args.secret or "",
            rds=args.rds or "",
            host=args.host,
            port=args.port,
            username=args.username or "postgres",
            password=args.password or "postgres",
            returnType=args.return_type,
        )

        if args.output:
            if args.format == "json":
                import json

                if isinstance(result, pd.DataFrame):
                    result.to_json(args.output, orient="records", indent=2)
                else:
                    with open(args.output, "w") as f:
                        json.dump(result, f, indent=2, default=str)
            elif isinstance(result, pd.DataFrame):
                result.to_csv(args.output, index=False)
            else:
                print("CSV output only supported for DataFrames", file=sys.stderr)
                sys.exit(1)
            print(f"Results written to {args.output}")
        elif isinstance(result, pd.DataFrame):
            print(result.to_string())
        else:
            print(result)

    except Exception as e:
        logger.exception(f"SQL operation failed: {e}")
        sys.exit(1)
