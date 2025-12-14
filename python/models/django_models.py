import datetime as dt
from decimal import Decimal
import ipaddress
import uuid

import pandas as pd

from _utils.common import basic  # Assumes custom utility for data type determination

# Descriptions of common Django model field types
django_model_field_desc = {
    "AutoField": "An integer field that automatically increments.",
    "BigAutoField": "A 64-bit integer field that automatically increments.",
    "BigIntegerField": "A 64-bit integer field.",
    "BinaryField": "A field to store binary data.",
    "BooleanField": "A boolean (True/False) field.",
    "CharField": "A field to store a fixed-length string.",
    "DateField": "A field to store a date (year, month, day).",
    "DateTimeField": "A field to store a date and time.",
    "DecimalField": "A fixed-precision decimal field.",
    "DurationField": "A field to store a duration of time.",
    "EmailField": "A field to store an email address.",
    "FileField": "A field to upload files.",
    "FloatField": "A floating-point number field.",
    "ImageField": "A field to upload image files.",
    "IntegerField": "An integer field.",
    "GenericIPAddressField": "A field to store an IPv4 or IPv6 address.",
    "PositiveIntegerField": "An integer field that only allows positive values.",
    "PositiveSmallIntegerField": "A smaller integer field that only allows positive values.",
    "SlugField": "A field to store URL-friendly strings.",
    "SmallIntegerField": "A smaller integer field.",
    "TextField": "A field to store long text.",
    "TimeField": "A field to store time.",
    "URLField": "A field to store a URL.",
    "ForeignKey": "A field to define a many-to-one relationship.",
    "ManyToManyField": "A field to define a many-to-many relationship.",
    "OneToOneField": "A field to define a one-to-one relationship.",
    "UUIDField": "A field to store a universally unique identifier (UUID).",
    "HStoreField": "A field to store key-value pairs in a dictionary-like format (requires PostgreSQL).",
    "JSONField": "A field to store JSON data (requires PostgreSQL or MariaDB 10.2+).",
    "XMLField": "A field to store XML data (requires PostgreSQL).",
    "ArrayField": "A field to store arrays of data (requires PostgreSQL).",
}

# Mapping of Django model fields to Python types
django_model_field_types = {
    "AutoField": int,
    "BigAutoField": int,
    "BigIntegerField": int,
    "BinaryField": bytes,
    "BooleanField": bool,
    "CharField": str,
    "DateField": dt.date,
    "DateTimeField": dt.datetime,
    "DecimalField": Decimal,
    "DurationField": dt.timedelta,
    "EmailField": str,
    "FileField": None,  # Depends on file type
    "FloatField": float,
    "ImageField": None,  # Depends on image type
    "IntegerField": int,
    "GenericIPAddressField": str,
    "PositiveIntegerField": int,
    "PositiveSmallIntegerField": int,
    "SlugField": str,
    "SmallIntegerField": int,
    "TextField": str,
    "TimeField": dt.time,
    "URLField": str,
    "ForeignKey": None,  # Depends on related model
    "ManyToManyField": None,  # Depends on related model
    "OneToOneField": None,  # Depends on related model
    "UUIDField": uuid.UUID,
    "HStoreField": dict,
    "JSONField": dict,
    "XMLField": str,
    "ArrayField": list,
}

# Mapping of Python types to Django model field declarations
python_to_django_model_field_types = {
    str: "models.CharField(max_length=255)",
    type(None): "models.CharField(max_length=255)",  # Treat None as a CharField for simplicity
    bool: "models.BooleanField()",
    bytes: "models.BinaryField()",
    dt.date: "models.DateField()",
    dt.datetime: "models.DateTimeField()",
    dt.time: "models.TimeField()",
    list: "models.TextField()",  # Assuming list gets serialized to text
    dict: "models.JSONField()",
    uuid.UUID: "models.UUIDField()",
    int: "models.IntegerField()",
    float: "models.FloatField()",
    ipaddress.IPv4Address: "models.GenericIPAddressField(protocol='IPv4')",
    ipaddress.IPv6Address: "models.GenericIPAddressField(protocol='IPv6')",
}


# Convert a Python value to its corresponding Django model field type
def value_to_model_field_type(value):
    value = basic.get_best_data_type(value)  # Get best-fit data type using custom logic
    for python_type, model_field_type in python_to_django_model_field_types.items():
        if isinstance(value, python_type):
            return model_field_type
    return None  # If no matching type, return None


# Convert a dictionary of data to Django model field types
def dict_to_model_field_type(data):
    output_data = {}
    for key, value in data.items():
        model_field_type = value_to_model_field_type(value)
        if model_field_type:
            output_data[key] = model_field_type
    return output_data


# Generate Django model class code from a dictionary
def dict_to_model_class(table_name, data):
    # Clean and prepare the data for model generation
    data = format_model_dict(table_name, data)

    # Start building the model class definition
    output_str = f"""class {table_name}(models.Model):\n"""
    output_str += "\t" + "id = models.AutoField(primary_key=True)\n"

    # Generate fields for each key in the data dictionary
    output_data = dict_to_model_field_type(data)
    for k, v in output_data.items():
        output_str += "\t" + k + " = " + v + "\n"

    return output_str


# Format dictionary keys and handle null values for model generation
def format_model_dict(table_name, data):
    data = {
        k.lower().replace(".", "_"): v for k, v in data.items()
    }  # Convert keys to lowercase and replace '.' with '_'
    new_data = {}

    # Check if 'id' key exists, rename it if necessary
    if "id" in data and f"{table_name.lower()}_id" not in data:
        new_data[f"{table_name.lower()}_id"] = data["id"]
        del data["id"]

    # Handle None or null values in the dictionary
    for k, v in data.items():
        new_data[k] = "" if v is None or pd.isna(v) or pd.isnull(v) else v

    return new_data
