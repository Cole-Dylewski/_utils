# %% [markdown]
# ## Coding Cheat Sheet
import base64
import datetime as dt
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
import json  # for json.dumps fallback
import os
from pathlib import Path
from typing import Any
from uuid import UUID

import numpy as np
import pandas as pd

# %%
getAllLockedQueriesOnRedshift = """select a.txn_owner, a.txn_db, a.xid, a.pid, a.txn_start, a.lock_mode, a.relation as table_id,nvl(trim(c."name"),d.relname) as tablename, a.granted,b.pid as blocking_pid ,datediff(s,a.txn_start,getdate())/86400||' days '||datediff(s,a.txn_start,getdate())%86400/3600||' hrs '||datediff(s,a.txn_start,getdate())%3600/60||' mins '||datediff(s,a.txn_start,getdate())%60||' secs' as txn_duration
from svv_transactions a
left join (select pid,relation,granted from pg_locks group by 1,2,3) b
on a.relation=b.relation and a.granted='f' and b.granted='t'
left join (select * from stv_tbl_perm where slice=0) c
on a.relation=c.id
left join pg_class d on a.relation=d.oid
where  a.relation is not null;"""
deleteQuery = """select pg_terminate_backend(pid);"""

# %%
# f"Python Datetime as SQL TimeStamp {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

"get row / column value"
# df.iloc[i]['column name']

"time format conversions"
# records['TIMESTAMP'] = [dt.datetime.strptime(ts, '%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d %H:%M:%S') for ts in records['TIMESTAMP'].to_list() ]
# [dt.datetime.fromtimestamp(x/1000, tz =pytz.timezone('UTC')).strftime("%Y-%m-%d") for x in data['Ad Begin Date'].to_list()]


"print in aws Lambda without generating a new log for each line"
# print(awsLambdaMultiLineStr.replace('\n','\r'))

"convert dataframe to list of dictionaries"
# df.to_dict('records')

"sort dataframe"
# df.sort_values(by=['col1', 'col2'], ascending = True)

"Time a process"
# from time import perf_counter
# t1_start = perf_counter()

# t_stop = perf_counter()
# print("export_blacklist Runtime:",t_stop-t1_start)

"load data from s3"
# obj = s3_client.get_object(Bucket=bucket, Key=key)
# data = obj.get("Body")ar

"detect if field is date time and convert to specific format"
# from urllib import parse
# pd.to_datetime('2023-10-12 00:30:00').replace(hour=12, minute=00).strftime('%Y-%m-%d %X')

"print out all imported modules"
# modulenames = set(set(sys.modules) & set(globals()))
# for name in modulenames:
#     print(name)


# %%
def get_uuid(uuidVer=4, format="str"):
    import uuid

    if uuidVer == 4:
        id = uuid.uuid4()
    if format.lower() == "str":
        return str(id)
    if format.lower() == "hex":
        return id.hex
    return None


# %%
def get_list_of_words():
    import requests

    word_site = "https://www.mit.edu/~ecprice/wordlist.10000"
    f = requests.get(word_site)
    return f.text.split("\n")


# %%
def print_nested(data, indent=0):
    """Prints a nested structure (dict, list, set, tuple) in a JSON-like readable format."""

    tab = "\t" * indent

    if isinstance(data, (list, set, tuple)):
        open_char, close_char = ("[", "]") if isinstance(data, (list, tuple)) else ("{", "}")
        print(f"{tab}{open_char}")
        for item in data:
            if isinstance(item, (dict, list, set, tuple)):
                print_nested(item, indent + 1)
            elif item is None:
                print(f"{tab}\tnull,")
            elif isinstance(item, bool):
                print(f"{tab}\t{'true' if item else 'false'},")
            elif isinstance(item, (int, float)):
                print(f"{tab}\t{item},")
            else:
                print(f'{tab}\t"{item}",')
        print(f"{tab}{close_char}")
        return

    if isinstance(data, dict):
        if indent == 0:
            print("{")

        for key, value in data.items():
            print(f'{tab}\t"{key}": ', end="")

            if isinstance(value, dict):
                print("{")
                print_nested(value, indent + 1)
                print(f"{tab}\t}},")

            elif isinstance(value, (list, set, tuple)):
                open_char, close_char = (
                    ("[", "]") if isinstance(value, (list, tuple)) else ("{", "}")
                )
                print(f"{open_char}")
                for item in value:
                    if isinstance(item, (dict, list, set, tuple)):
                        print_nested(item, indent + 2)
                    elif item is None:
                        print(f"{tab}\t\tnull,")
                    elif isinstance(item, bool):
                        print(f"{tab}\t\t{'true' if item else 'false'},")
                    elif isinstance(item, (int, float)):
                        print(f"{tab}\t\t{item},")
                    else:
                        print(f'{tab}\t\t"{item}",')
                print(f"{tab}\t{close_char},")

            elif value is None:
                print("null,")

            elif isinstance(value, bool):
                print(f"{'true' if value else 'false'},")

            elif isinstance(value, (int, float)):
                print(f"{value},")

            else:
                print(f'"{value}",')

        if indent == 0:
            print("}")


def format_nested(data, indent=0):
    """Returns a JSON-like multi-line string representation of a nested structure."""

    lines = []
    tab = "\t" * indent

    if isinstance(data, (list, set, tuple)):
        open_char, close_char = ("[", "]") if isinstance(data, (list, tuple)) else ("{", "}")
        lines.append(f"{tab}{open_char}")
        for item in data:
            if isinstance(item, (dict, list, set, tuple)):
                lines.append(format_nested(item, indent + 1))
            elif item is None:
                lines.append(f"{tab}\tnull,")
            elif isinstance(item, bool):
                lines.append(f"{tab}\t{'true' if item else 'false'},")
            elif isinstance(item, (int, float)):
                lines.append(f"{tab}\t{item},")
            else:
                lines.append(f'{tab}\t"{item}",')
        lines.append(f"{tab}{close_char}")
        return "\n".join(lines)

    if isinstance(data, dict):
        if indent == 0:
            lines.append("{")

        for key, value in data.items():
            line = f'{tab}\t"{key}": '

            if isinstance(value, dict):
                line += "{"
                lines.append(line)
                lines.append(format_nested(value, indent + 1))
                lines.append(f"{tab}\t}},")

            elif isinstance(value, (list, set, tuple)):
                open_char, close_char = (
                    ("[", "]") if isinstance(value, (list, tuple)) else ("{", "}")
                )
                lines.append(f"{line}{open_char}")
                for item in value:
                    if isinstance(item, (dict, list, set, tuple)):
                        lines.append(format_nested(item, indent + 2))
                    elif item is None:
                        lines.append(f"{tab}\t\tnull,")
                    elif isinstance(item, bool):
                        lines.append(f"{tab}\t\t{'true' if item else 'false'},")
                    elif isinstance(item, (int, float)):
                        lines.append(f"{tab}\t\t{item},")
                    else:
                        lines.append(f'{tab}\t\t"{item}",')
                lines.append(f"{tab}\t{close_char},")

            elif value is None:
                lines.append(f"{line}null,")

            elif isinstance(value, bool):
                lines.append(f"{line}{'true' if value else 'false'},")

            elif isinstance(value, (int, float)):
                lines.append(f"{line}{value},")

            else:
                lines.append(f'{line}"{value}",')

        if indent == 0:
            lines.append("}")

    return "\n".join(lines)


# %%


def print_folder_structure(
    start_path: str, indent_level: int = 0, file=None, fancy_format: bool = False
) -> None:
    """Recursively prints or writes the folder structure starting from start_path."""
    indent = ("|   " if fancy_format else "    ") * indent_level
    dir_format = f"{indent}+-- {{}}/\n" if fancy_format else f"{indent}{{}}/\n"
    file_format = f"{indent}+-- {{}}\n" if fancy_format else f"{indent}{{}}\n"

    try:
        for item in sorted(os.listdir(start_path)):  # Sort items for consistent output
            item_path = os.path.join(start_path, item)
            line = dir_format.format(item) if os.path.isdir(item_path) else file_format.format(item)

            # Write to file or print based on the presence of the file object
            if file:
                file.write(line)
            else:
                print(line, end="")

            # Recursively print subdirectories
            if os.path.isdir(item_path):
                print_folder_structure(item_path, indent_level + 1, file, fancy_format)
    except PermissionError:
        error_msg = f"{indent}[Permission Denied: {start_path}]\n"
        if file:
            file.write(error_msg)
        else:
            print(error_msg, end="")


def output_folder_structure(
    start_path: str, output_file_path: str | None = None, fancy_format: bool = False
) -> None:
    """Outputs the folder structure to a file if specified, or prints it."""
    if not os.path.exists(start_path):
        print(f"Error: The path '{start_path}' does not exist.")
        return

    if output_file_path:
        try:
            with open(output_file_path, "w") as file:
                print_folder_structure(start_path, file=file, fancy_format=fancy_format)
            print(f"Folder structure written to '{output_file_path}'.")
        except OSError as e:
            print(f"Error writing to file '{output_file_path}': {e}")
    else:
        print_folder_structure(start_path, fancy_format=fancy_format)


# Example usage:
# To print to console with default format:
# output_folder_structure('/path/to/your/directory')

# To print to console with fancy format:
# output_folder_structure('/path/to/your/directory', fancy_format=True)

# To write to a file with fancy format:
# output_folder_structure('/path/to/your/directory', 'output.txt', fancy_format=True)


# Text color dictionary
def color_print(styles):
    """
    Concatenate strings with specified text and background colors and print them in one line.

    :param styles: List of dictionaries containing:
                   - 'string': Text to print (required)
                   - 'text': Text color key from text_colors (optional)
                   - 'background': Background color key from background_colors (optional)
                   - 'reset': Boolean, whether to reset styles after the string (default True)
    """
    # Expanded color dictionaries
    text_colors = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "bright_black": "\033[90m",
        "bright_red": "\033[91m",
        "bright_green": "\033[92m",
        "bright_yellow": "\033[93m",
        "bright_blue": "\033[94m",
        "bright_magenta": "\033[95m",
        "bright_cyan": "\033[96m",
        "bright_white": "\033[97m",
        "orange": "\033[38;5;202m",
        "pink": "\033[38;5;205m",
        "lime": "\033[38;5;154m",
        "teal": "\033[38;5;44m",
        "purple": "\033[38;5;93m",
        "brown": "\033[38;5;94m",
        "gold": "\033[38;5;220m",
        "silver": "\033[38;5;250m",
        "coral": "\033[38;5;210m",
        "navy": "\033[38;5;17m",
        "peach": "\033[38;5;216m",
        "ivory": "\033[38;5;230m",
        "turquoise": "\033[38;5;49m",
        "emerald": "\033[38;5;40m",
        "charcoal": "\033[38;5;240m",
        "sky_blue": "\033[38;5;117m",
        "rose": "\033[38;5;213m",
        "mint": "\033[38;5;122m",
        "khaki": "\033[38;5;187m",
        "violet": "\033[38;5;177m",
        "beige": "\033[38;5;230m",
        "crimson": "\033[38;5;197m",
        "aqua": "\033[38;5;123m",
        "salmon": "\033[38;5;209m",
    }
    background_colors = {
        "black": "\033[40m",
        "red": "\033[41m",
        "green": "\033[42m",
        "yellow": "\033[43m",
        "blue": "\033[44m",
        "magenta": "\033[45m",
        "cyan": "\033[46m",
        "white": "\033[47m",
        "bright_black": "\033[100m",
        "bright_red": "\033[101m",
        "bright_green": "\033[102m",
        "bright_yellow": "\033[103m",
        "bright_blue": "\033[104m",
        "bright_magenta": "\033[105m",
        "bright_cyan": "\033[106m",
        "bright_white": "\033[107m",
        "orange": "\033[48;5;202m",
        "pink": "\033[48;5;205m",
        "lime": "\033[48;5;154m",
        "teal": "\033[48;5;44m",
        "purple": "\033[48;5;93m",
        "brown": "\033[48;5;94m",
        "gold": "\033[48;5;220m",
        "silver": "\033[48;5;250m",
        "coral": "\033[48;5;210m",
        "navy": "\033[48;5;17m",
        "peach": "\033[48;5;216m",
        "ivory": "\033[48;5;230m",
        "turquoise": "\033[48;5;49m",
        "emerald": "\033[48;5;40m",
        "charcoal": "\033[48;5;240m",
        "sky_blue": "\033[48;5;117m",
        "rose": "\033[48;5;213m",
        "mint": "\033[48;5;122m",
        "khaki": "\033[48;5;187m",
        "violet": "\033[48;5;177m",
        "beige": "\033[48;5;230m",
        "crimson": "\033[48;5;197m",
        "aqua": "\033[48;5;123m",
        "salmon": "\033[48;5;209m",
    }
    reset_code = "\033[0m"

    result = ""
    for style in styles:
        string = style.get("string", "")
        text_color = text_colors.get(style.get("text", ""), "")
        background_color = background_colors.get(style.get("background", ""), "")
        reset = style.get("reset", True)

        # Build the styled string
        styled_string = f"{text_color}{background_color}{string}"
        if reset:
            styled_string += reset_code
        result += styled_string

    # Print the concatenated result
    print(result)


# # Example Usage
# styles = [
#     {"string": "Hello", "text": "red", "background": "yellow", "reset": True},
#     {"string": " ", "reset": False},  # Space
#     {"string": "World!", "text": "lime", "background": "navy", "reset": True},
#     {"string": " Python is colorful.", "text": "violet", "background": "beige", "reset": True},
# ]

# color_print(styles)


# %%
def flatten_dict(nested_dict, parent_key="", sep="_"):
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
            items[new_key] = ",".join(str(item) for item in value)
        elif isinstance(value, dt.datetime):
            # Convert datetime objects to ISO-formatted strings
            items[new_key] = value.isoformat()
        else:
            items[new_key] = value
    return items


def serialize_value(value: Any) -> Any:
    """
    Recursively convert a value to a JSON-serializable format.
    """

    # Handle Decimal
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)

    # Handle floats (native & numpy)
    if isinstance(value, (float, np.floating)):
        return int(value) if float(value).is_integer() else float(value)

    # Handle ints (native & numpy)
    if isinstance(value, (int, np.integer)):
        return int(value)

    # Handle None and pandas/numpy null types
    if value is None or value is pd.NA or (pd.api.types.is_scalar(value) and pd.isna(value)):
        return None

    # Handle datetime objects
    if isinstance(value, (datetime, date)):
        return value.isoformat()

    # Handle numpy datetime64 and pandas Timestamp
    if isinstance(value, (np.datetime64, pd.Timestamp)):
        # Convert to pandas.Timestamp and then isoformat
        return pd.to_datetime(value).isoformat()

    # UUID -> string
    if isinstance(value, UUID):
        return str(value)

    # Path -> string
    if isinstance(value, Path):
        return str(value)

    # Sets -> lists
    if isinstance(value, (set, frozenset)):
        return [serialize_value(item) for item in value]

    # Bytes -> base64 encoded string
    if isinstance(value, (bytes, bytearray)):
        return base64.b64encode(value).decode("utf-8")

    # Complex numbers -> dict with real & imag
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}

    # Enum -> its value
    if isinstance(value, Enum):
        return value.value

    # Numpy arrays & Pandas Series -> lists
    if isinstance(value, (np.ndarray, pd.Series)):
        return [serialize_value(item) for item in value]

    # Dict -> recursively process key-values
    if isinstance(value, dict):
        return {str(k): serialize_value(v) for k, v in value.items()}

    # Lists/Tuples -> recursively process items
    if isinstance(value, (list, tuple)):
        return [serialize_value(item) for item in value]

    # Fallback for objects with __dict__
    if hasattr(value, "__dict__"):
        return serialize_value(vars(value))

    # Fallback to string if it's not JSON serializable
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return str(value)


def make_serializable(data: dict[str, Any] | list[Any] | Any) -> dict[str, Any] | list[Any] | Any:
    """
    Converts complex/nested data structures to JSON serializable ones.
    """
    if isinstance(data, dict):
        return {k: serialize_value(v) for k, v in data.items()}

    if isinstance(data, list):
        return [serialize_value(item) for item in data]

    return serialize_value(data)
