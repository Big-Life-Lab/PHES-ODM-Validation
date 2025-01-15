from typing import List, Optional

from rich.console import Console
from rich.pretty import pprint
from rich.table import Table

from odm_validation.utils import (
    import_dataset,
    import_json_file,
    import_yaml_file,
)


def pprint_dict_list(dict_list: List[dict], title: str,
                     ignore_prefix: Optional[str] = None):
    """
    Pretty prints a list of dictionaries in the console to look like a table

    dict_list: The list of dictionaries
    title: The title of the table printed along with the table
    """
    table = Table(title=title, expand=True)

    dict_keys = list(
        filter(lambda k: not (ignore_prefix and k.startswith(ignore_prefix)),
               dict_list[0].keys()))
    for column_name in dict_keys:
        table.add_column(column_name)

    for current_dict in dict_list:
        row = []
        for column_name in dict_keys:
            row.append(current_dict[column_name])
        table.add_row(*row)

    console = Console()
    console.print(table)


def pprint_csv_file(file_path: str, title: str, ignore_prefix=None):
    dataset = import_dataset(file_path)
    pprint_dict_list(dataset, title, ignore_prefix)


def pprint_json_file(file_path: str):
    data = import_json_file(file_path)
    pprint(data, expand_all=True)


def pprint_yaml_file(file_path: str):
    yaml_file = import_yaml_file(file_path)

    pprint(yaml_file, expand_all=True)
