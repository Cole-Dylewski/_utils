import json
import datetime
# %%
def flatten_dict(nested_dict, parent_key='', sep='_'):
    """
    Recursively flattens a nested dictionary.

    :param nested_dict: The dictionary to flatten.
    :param parent_key: The base key string (used during recursion).
    :param sep: Separator used to join keys.
    :return: A flattened dictionary with concatenated keys.
    """
    items = {}
    for key, value in nested_dict.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            # Recursively flatten nested dictionaries
            items.update(flatten_dict(value, new_key, sep=sep))
        elif isinstance(value, list):
            # If it's a list, convert it to a comma-separated string
            items[new_key] = ','.join(str(item) for item in value)
        elif isinstance(value, datetime.datetime):
            # Convert datetime objects to ISO-formatted strings
            items[new_key] = value.isoformat()
        else:
            items[new_key] = value
    return items