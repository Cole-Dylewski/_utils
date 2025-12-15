import logging
from typing import Any

from boto3.dynamodb.conditions import Attr, Key
from botocore.config import Config
from botocore.exceptions import ClientError

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Retry configuration for DynamoDB operations
retry_config = Config(retries={"max_attempts": 5, "mode": "standard"})


class DynamoDBHandler:
    """
    DynamoDBHandler with AWS session management, error handling, and logging.
    """

    def __init__(
        self, aws_access_key_id=None, aws_secret_access_key=None, region_name=None, session=None
    ):
        try:
            # get aws boto3 session
            if session:
                self.session = session
            else:
                from aws import boto3_session

                self.session = boto3_session.Session(
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    region_name=region_name,
                )
            self.dynamodb_resource = self.session.resource("dynamodb")
            self.dynamodb_client = self.session.client("dynamodb", config=retry_config)
            logger.info("Connected to AWS DynamoDB")
        except ClientError as e:
            logger.exception(f"Failed to initialize DynamoDB client: {e}")
            raise

    def convert_dynamodb_values(
        self, attributes: list[dict[str, Any]], attribute_values: dict[str, Any]
    ) -> dict[str, Any]:
        """Convert values to match DynamoDB attribute types."""
        dynamodb_to_python = {
            "S": str,
            "N": (int, float),
            "B": bytes,
            "BOOL": bool,
            "NULL": type(None),
            "SS": set,
            "NS": set,
            "BS": set,
            "M": dict,
            "L": list,
        }

        converted_values = {}
        for attribute in attributes:
            attribute_name = attribute["AttributeName"]
            attribute_type = attribute["AttributeType"]
            value = attribute_values.get(attribute_name)

            if value is not None:
                if attribute_type == "N" and isinstance(value, str):
                    try:
                        value = int(value) if "." not in value else float(value)
                    except ValueError:
                        logger.warning(f"Value '{value}' cannot be converted to int or float")
                elif attribute_type not in dynamodb_to_python:
                    logger.warning(
                        f"Unsupported attribute type '{attribute_type}' for attribute '{attribute_name}'"
                    )
                    continue

                converted_values[attribute_name] = dynamodb_to_python.get(attribute_type, str)(
                    value
                )

        return converted_values

    def get_table_metadata(self, table_name: str) -> dict[str, Any]:
        """Retrieve metadata for a DynamoDB table."""
        try:
            response = self.dynamodb_client.describe_table(TableName=table_name)
            logger.info(f"Retrieved metadata for table {table_name}")
            return response.get("Table", {})
        except ClientError as e:
            logger.exception(f"Failed to retrieve table metadata: {e.response['Error']['Message']}")
            return {}

    def update_record(
        self, table_name: str, key: dict[str, Any], attributes: dict[str, Any]
    ) -> dict[str, Any]:
        """Update or create a record in a DynamoDB table."""
        table = self.dynamodb_resource.Table(table_name)
        try:
            update_expr = "SET " + ", ".join(f"{k}=:{k}" for k in attributes)
            expr_attr_values = {f":{k}": v for k, v in attributes.items()}
            response = table.update_item(
                Key=key,
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_attr_values,
                ReturnValues="ALL_NEW",
            )
            logger.info(f"Record updated in table {table_name} with key {key}")
            return response["Attributes"]
        except ClientError as e:
            logger.exception(f"Failed to update record: {e.response['Error']['Message']}")
            raise

    def get_records(
        self, table_name: str, key_id: Any | None = None, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Query or scan a DynamoDB table based on the provided parameters.
        """
        table = self.dynamodb_resource.Table(table_name)
        items = []
        try:
            if key_id is not None:
                response = table.query(KeyConditionExpression=Key("id").eq(key_id))
                items.extend(response.get("Items", []))
                while "LastEvaluatedKey" in response:
                    response = table.query(
                        KeyConditionExpression=Key("id").eq(key_id),
                        ExclusiveStartKey=response["LastEvaluatedKey"],
                    )
                    items.extend(response.get("Items", []))

            elif filters:
                filter_expression = Attr(next(iter(filters.keys()))).eq(
                    next(iter(filters.values()))
                )
                for key, value in list(filters.items())[1:]:
                    filter_expression = filter_expression & Attr(key).eq(value)

                response = table.scan(FilterExpression=filter_expression)
                items.extend(response.get("Items", []))
                while "LastEvaluatedKey" in response:
                    response = table.scan(
                        FilterExpression=filter_expression,
                        ExclusiveStartKey=response["LastEvaluatedKey"],
                    )
                    items.extend(response.get("Items", []))

            else:
                response = table.scan()
                items.extend(response.get("Items", []))
                while "LastEvaluatedKey" in response:
                    response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
                    items.extend(response.get("Items", []))

            logger.info(f"Retrieved {len(items)} records from table {table_name}")
            return items
        except ClientError as e:
            logger.exception(
                f"Error querying or scanning table {table_name}: {e.response['Error']['Message']}"
            )
            return []

    def delete_all_records(self, table_name: str, limit: int | None = None):
        """
        Deletes all records in a DynamoDB table, with optional limit.
        """
        table = self.dynamodb_resource.Table(table_name)
        try:
            deleted_count = 0
            response = table.scan()
            data = response.get("Items", [])

            # Retrieve all key attributes from the table schema
            key_schema = table.key_schema
            key_attributes = [key["AttributeName"] for key in key_schema]
            logger.info(f"Key attributes for deletion: {key_attributes}")

            with table.batch_writer() as batch:
                for item in data:
                    if limit and deleted_count >= limit:
                        logger.info(f"Deleted {deleted_count} items, reached limit")
                        return

                    # Build the key dictionary dynamically based on the schema
                    key = {attr: item[attr] for attr in key_attributes}
                    batch.delete_item(Key=key)
                    deleted_count += 1

            while "LastEvaluatedKey" in response:
                response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
                data = response.get("Items", [])
                with table.batch_writer() as batch:
                    for item in data:
                        if limit and deleted_count >= limit:
                            logger.info(f"Deleted {deleted_count} items, reached limit")
                            return

                        # Build the key dictionary dynamically
                        key = {attr: item[attr] for attr in key_attributes}
                        batch.delete_item(Key=key)
                        deleted_count += 1

            logger.info(f"All records deleted from table {table_name}. Total: {deleted_count}")

        except ClientError as e:
            logger.exception(
                f"Failed to delete items from {table_name}. Error: {e.response['Error']['Message']}"
            )
            raise

    def push_record(self, table_name: str, record: dict[str, Any]) -> dict[str, Any]:
        """
        Push a record to a DynamoDB table.
        """
        table = self.dynamodb_resource.Table(table_name)
        try:
            response = table.put_item(Item=record)
            logger.info(f"Record pushed to table {table_name}")
            return response
        except ClientError as e:
            logger.exception(
                f"Failed to push record to {table_name}. Error: {e.response['Error']['Message']}"
            )
            return {"Error": e.response["Error"]["Message"]}

    def push_bulk_records(self, table_name: str, records: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Push bulk records to a DynamoDB table.
        """
        table = self.dynamodb_resource.Table(table_name)
        try:
            with table.batch_writer() as batch:
                for record in records:
                    batch.put_item(Item=record)
            logger.info(f"{len(records)} records pushed to table {table_name}")
            return {"message": f"{len(records)} records pushed to table {table_name}"}
        except ClientError as e:
            logger.exception(
                f"Failed to push bulk records to {table_name}. Error: {e.response['Error']['Message']}"
            )
            return {"Error": e.response["Error"]["Message"]}
