from typing import List

from rich.table import Table
from rich.console import Console
def pprint_dict_list(dict_list: List[dict], title: str):
    """
    Pretty prints a list of dictionaries in the console to look like a table

    dict_list: The list of dictionaries
    title: The title of the table printed along with the table
    """
    table = Table(title = title, expand = True)

    dict_keys = dict_list[0].keys()
    for column_name in dict_keys:
        table.add_column(column_name)

    for current_dict in dict_list:
        row = []
        for column_name in dict_keys:
            row.append(current_dict[column_name])
        table.add_row(*row)
    
    console = Console()
    console.print(table)

import json
def import_json(file_path: str) -> dict:
    file = open(file_path)
    json_str = file.read()
    file.close()
    return json.loads(json_str)