import json
import operator
from functools import reduce
from typing import Any, List


def get_len(x: Any) -> int:
    """Returns len if possible, otherwise zero."""
    return len(x) if getattr(x, '__len__', None) else 0


# TODO: swap src and dst to make the first arg the mutable one
def deep_update(src: dict, dst: dict):
    """
    Recursively update a dict.
    Subdict's won't be overwritten but also updated.
    List values will be joined, but not recursed.

    Warning: List items may be duplicated.

    Originally from: https://stackoverflow.com/a/8310229
    """
    for key, value in src.items():
        if key not in dst:
            dst[key] = value
        elif isinstance(value, dict):
            deep_update(value, dst[key])
        elif isinstance(value, list):
            src_list = value
            if len(src_list) > 0:
                dst_list = dst[key]
                dst_list += src_list


def hash_dict(d) -> str:
    json.dumps(d, sort_keys=True)


def deduplicate_dict_list(dicts: List[dict]) -> List[dict]:
    assert isinstance(dicts, list)
    assert len(dicts) == 0 or isinstance(dicts[0], dict)
    hashes = map(hash_dict, dicts)
    unique_dict = dict(zip(hashes, dicts))
    return list(unique_dict.values())


def strip_dict_key(d: dict, target_key: str):
    """Recursively strips `d` of `target_key` entries."""
    assert isinstance(d, dict)
    for key, val in list(d.items()):
        if key == target_key:
            del d[key]
        elif isinstance(val, dict):
            strip_dict_key(val, target_key)
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, dict):
                    strip_dict_key(item, target_key)
    return d


def flatten(x: List[List[Any]]) -> List[Any]:
    return reduce(operator.iconcat, x, [])
