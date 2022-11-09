from typing import List
from rich.table import Table
from rich.console import Console
from utils import import_dataset, import_yaml_file
import json
from rich.pretty import pprint


def pprint_dict_list(dict_list: List[dict], title: str):
    """
    Pretty prints a list of dictionaries in the console to look like a table

    dict_list: The list of dictionaries
    title: The title of the table printed along with the table
    """
    table = Table(title=title, expand=True)

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


def import_json(file_path: str) -> dict:
    file = open(file_path)
    json_str = file.read()
    file.close()
    return json.loads(json_str)


def pprint_csv_file(file_path: str, title: str):
    dataset = import_dataset(file_path)
    pprint_dict_list(dataset, title)


def pprint_json_file(file_path: str):
    json_file = open(file_path)
    json_str = json_file.read()
    json_file.close()

    pprint(json.loads(json_str), expand_all=True)


def pprint_yaml_file(file_path: str):
    yaml_file = import_yaml_file(file_path)

    pprint(yaml_file, expand_all=True)
