import re
import sys
import json


class Queue:
    def __init__(self, init=None):
        self._items = init if init is not None else []

    def __repr__(self) -> str:
        return '[' + ', '.join([repr(i) for i in self._items]) + ']'

    def pop(self) -> str:
        return self._items.pop(0)


class InvalidPathOrExpression(Exception):
    def __init__(self, *args):
        msg = f"Invalid path or expression: '{args[0]}'"
        if len(args) > 1:
            msg += '\n\t'
            msg += '\n\t'.join(args[1:])

        super().__init__(msg)


def get_args():
    root = sys.argv[1]
    jql_tokens = sys.argv[2:]

    return root, jql_tokens


def get_json(path: str) -> dict:
    with open(path, 'r') as fin:
        data = json.load(fin)

    return data


# (operator, # of params)
# Arranged in order of operations
OPS = [
    ('-not', 1),
    ('-and', 2),
    ('-or', 2),
    ('-ex', 1),
    ('-nex', 1),
    ('-in', 2),
    ('-nin', 2),
    ('-eq', 2),
    ('-ne', 2),
    ('-mt', 2),
    ('-rx', 2),
    ('-lt', 2),
    ('-le', 2),
    ('-gt', 2),
    ('-ge', 2),
    ('-len', 1),
    ('-obj', 1),
    ('-arr', 1),
    ('-str', 1),
    ('-num', 1)
]
ALL_OPS = set(map(lambda t: t[0], OPS))


def create_tree(tokens: Queue) -> dict:
    # Key = op
    # Value = dict/tuple
    curr = tokens.pop()

    if curr not in ALL_OPS:
        if curr.isnumeric():
            return float(curr) if '.' in curr else int(curr)

        if curr.lower() == 'true':
            return True

        if curr.lower() == 'false':
            return False

        return curr

    curr = curr

    for op, num_args in OPS:
        if curr == op:
            retv = {}
            args = tuple( create_tree(tokens) for _ in range(num_args) )
            retv[op] = args

            return retv

    raise RuntimeError(f"Unable to parse '{curr}' (this should never happen).")


ARRAY_PATH_REGEX = re.compile(r'^(?P<path>[A-Za-z0-9]+)\[(?P<idx>\d+)?\]$')
def get_value(json: dict, prop_path: str):
    curr = [json]
    for path_el in prop_path.split('.')[1:]:
        new_curr = []

        for el in curr:
            if m := ARRAY_PATH_REGEX.match(path_el):
                path = m['path']
                idx = m['idx']

                if path not in el:
                    return None

                elif idx is None:
                    new_curr += el[path]

                else:
                    idx = int(idx)

                    if len(el[path]) < idx:
                        return None
                    else:
                        new_curr.append(el[path][idx])

            elif path_el not in el:
                return None

            else:
                new_curr.append(el[path_el])

            curr = new_curr

    if isinstance(curr, str):
        curr = curr

    if isinstance(curr, list):
        curr = [evaluate(json, el) for el in curr]

    return curr


def some(callback, arr: list) -> bool:
    if isinstance(arr, list):
        for el in arr:
            if callback(el):
                return True
        return False

    return arr


PATH_REGEX = re.compile(r'^(\.[A-Za-z0-9]+(\[\d*\])?)+$')
def evaluate(json: dict, operator):
    # A String operator should always be a property-path
    if isinstance(operator, str):
        if PATH_REGEX.search(operator) is not None:
            value = get_value(json, operator)
            return value

        return operator

    # These are parameters, and need to be eval'd/returned individually
    if isinstance(operator, tuple):
        retv = tuple( evaluate(json, param) for param in operator )
        return retv

    # This is an actual operator
    if isinstance(operator, dict):
        for op in operator:
            params = operator[op]

            if op == '-not':
                param_0 = evaluate(json, params[0])

                return some(lambda p: not p, param_0)

            if op == '-and':
                param_0 = evaluate(json, params[0])
                if some(lambda p: not p, param_0):
                    return False

                param_1 = evaluate(json, params[1])

                return some(lambda p: p, param_1)

            if op == '-or':
                param_0 = evaluate(json, params[0])
                if some(lambda p: p, param_0):
                    return True

                param_1 = evaluate(json, params[1])

                return some(lambda p: p, param_1)

            if op == '-ex':
                param_0 = evaluate(json, params[0])

                return param_0 is not None

            if op == '-nex':
                param_0 = evaluate(json, params[0])

                return param_0 is None

            if op == '-in':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return some(lambda p: param_1 in p, param_0)

            if op == '-nin':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return some(lambda p: param_1 not in p, param_0)

            if op == '-eq':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                if isinstance(param_0, str):
                    return some(lambda p: p.lower() == param_1.lower(), param_0)

                return some(lambda p: p == param_1, param_0)

            if op == '-ne':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                if isinstance(param_0, str):
                    return some(lambda p: p.lower() != param_1.lower(), param_0)

                return some(lambda p: p != param_1, param_0)

            if op == '-mt' or op == '-rx':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                if param_0 is None:
                    return False

                if param_1 is None:
                    raise InvalidPathOrExpression(params[1], 'Invalid regular expression')

                return some(lambda p: re.search(param_1, p) is not None, param_0)

            if op == '-lt':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return some(lambda p: p < param_1, param_0)

            if op == '-le':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return some(lambda p: p <= param_1, param_0)

            if op == '-gt':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return some(lambda p: p > param_1, param_0)

            if op == '-ge':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return some(lambda p: p >= param_1, param_0)

            if op == '-len':
                param_0 = evaluate(json, params[0])

                return len(param_0)

            if op == '-obj':
                param_0 = evaluate(json, params[0])

                return some(lambda p: isinstance(p, dict), param_0)

            if op == '-arr':
                param_0 = evaluate(json, params[0])

                return some(lambda p: isinstance(p, list), param_0)

            if op == '-str':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return some(lambda p: isinstance(p, str), param_0)

            if op == '-num':
                param_0 = evaluate(json, params[0])

                return some(lambda p: isinstance(p, int) or isinstance(p, float), param_0)

    return operator


def main():
    json_path = sys.argv[1]
    token_queue = Queue(sys.argv[2:])

    tree = create_tree(token_queue)
    json_data = get_json(json_path)
    try:
        retv = evaluate(json_data, tree)
    except InvalidPathOrExpression as ipoe:
        return ipoe

    if not isinstance(retv, bool):
        raise TypeError(f"JQL does not resolve to a boolean (resolves to '{retv}')")

    return retv


if __name__ == "__main__":
    print(main())
