import dateutil.parser as dateutil_parser
import json
import operator
from datetime import datetime
from functools import reduce
from typing import Any, List, Optional, Union


def get_len(x: Any) -> int:
    """Returns len if possible, otherwise zero."""
    return len(x) if getattr(x, '__len__', None) else 0


def hash2(x) -> int:
    """An alternative hash function that can hash anything."""
    if isinstance(x, dict) or isinstance(x, list):
        return hash(json.dumps(x, sort_keys=True))
    else:
        return hash(x)


def deep_update(dst: dict, src: dict):
    """
    Recursively update a dict.
    Subdict's won't be overwritten but also updated.
    List values will be joined, but not recursed.

    Originally from: https://stackoverflow.com/a/8310229
    """
    for key, value in src.items():
        if key not in dst:
            dst[key] = value
        elif isinstance(value, dict):
            deep_update(dst[key], value)
        elif isinstance(value, list):
            src_list = value
            if len(src_list) == 0:
                continue
            dst_list = dst[key]
            dst_hashset = set(map(hash2, dst_list))
            for item in src_list:
                if hash2(item) not in dst_hashset:
                    dst_list.append(item)


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
    if val is None:
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


def quote(x: str) -> str:
    return f'"{x}"'


def countdown(count: int):
    "counts down from `count`-1 to 0"
    for i in range(count - 1, -1, -1):
        yield i


def iscollection(x) -> bool:
    assert not isinstance(x, set), "sets are not supported in this context"
    return isinstance(x, dict) or isinstance(x, list)


def swapDelete(items: list, i: int):
    '''swaps the item at `i` with the last element, and removes the last
    element.'''
    last = items.pop()
    if i < len(items):
        items[i] = last


def keep(x: Union[dict, list], target: str):
    '''Recursively removes all dict-keys and list-values not matching
    `target`.'''
    assert not isinstance(x, set)
    if isinstance(x, dict):
        for key in list(x):
            if key == target:
                continue
            val = x[key]
            if iscollection(val):
                keep(val, target)
                if len(val) == 0:
                    del x[key]
            elif key != target:
                del x[key]
    elif isinstance(x, list):
        i = 0
        while i < len(x):
            val = x[i]
            if iscollection(val):
                keep(val, target)
                if len(val) == 0:
                    swapDelete(x, i)
                    continue
            elif val != target:
                swapDelete(x, i)
                continue
            i += 1
