import dateutil.parser as dateutil_parser
import json
import operator
from datetime import datetime
from functools import reduce
from typing import Any, List, Optional


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


def deduplicate_list(items: List[Any]) -> List[Any]:
    return list(set(items))


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


def parse_datetime(s: str) -> datetime:
    if len(s) < len('yyyymmdd'):
        raise ValueError('datetime string is too short')
    return dateutil_parser.parse(s)


def parse_int(val) -> int:
    """Returns `val` as an int. A number with only zeroes as decimals also
    counts as an int. A ValueError is raised otherwise."""
    float_val = float(val)  # may raise
    int_val = int(float_val)
    if int_val == float_val:
        return int_val
    else:
        raise ValueError('not a valid integer')


def try_parse_int(val) -> Optional[int]:
    if not val:
        return
    try:
        return parse_int(val)
    except ValueError:
        pass


def try_parse_float(val) -> Optional[float]:
    if not val:
        return
    try:
        return float(val)
    except ValueError:
        pass


def type_name(type_class) -> str:
    result = type_class.__name__
    if result == 'int':
        result = 'integer'
    if result == 'str':
        result = 'string'
    return result


def inc(x):
    """Increment x by 1, as seen in Pascal."""
    return x + 1
