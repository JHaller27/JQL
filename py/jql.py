import re
import os
import sys
import json
import shlex
import logging
import argparse


logging.basicConfig()


class Queue:
    def __init__(self, init=None):
        self._items = init if init is not None else []

    def __repr__(self) -> str:
        return '[' + ', '.join([repr(i) for i in self._items]) + ']'

    def pop(self) -> str:
        return self._items.pop(0)

    def peek(self) -> str:
        return self._items[0]


class InvalidPathOrExpression(Exception):
    def __init__(self, *args):
        msg = f"Invalid path or expression: '{args[0]}'"
        if len(args) > 1:
            msg += '\n\t'
            msg += '\n\t'.join(args[1:])

        super().__init__(msg)


class Comparer:
    def compare(self, a, b) -> int:
        a = str(a)
        b = str(b)

        if a < b:
            return -1
        elif a > b:
            return 1
        else:
            return 0


class InsensitiveComparer(Comparer):
    def compare(self, a, b) -> int:
        a = str(a).lower()
        b = str(b).lower()

        return super().compare(a, b)


comparer = Comparer()


def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('root', type=str, help='Path to root to search for .json files')
    parser.add_argument('-r', '--recurse', action='store_true', help='Recursively search for files')
    parser.add_argument('-i', '--insensitive', action='store_true', help='Compare strings as case-insensitive (does not affect JSON paths)')
    parser.add_argument('-v', dest='verbosity', action='count', default=0, help='Increase level of logging (default: none)')

    args, jql_tokens = parser.parse_known_args()

    if len(jql_tokens) == 0:
        raw_in = input("JQL expression> ")
        jql_tokens = shlex.split(raw_in)

    return args, jql_tokens


def get_json(path: str) -> dict:
    logging.info("Loading '%s' as json", path)
    try:
        with open(path, 'r') as fin:
            data = json.load(fin)

    except UnicodeDecodeError:
        logging.debug("Using cp1252 encoding for '%s'", path)

        with open(path, 'r', encoding='cp1252') as fin:
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
    ('-num', 1),
    ('-bool', 1)
]
ALL_OPS = set(map(lambda t: t[0], OPS))


def create_tree(tokens: Queue) -> dict:
    logging.debug("Creating expression tree from '%s'...", tokens.peek())

    # Key = op
    # Value = dict/tuple
    curr = tokens.pop()

    if curr not in ALL_OPS:
        if curr.isnumeric():
            logging.debug("Parsing '%s' as number", curr)
            return float(curr) if '.' in curr else int(curr)

        if curr.lower() == 'true':
            logging.debug("Parsing '%s' as True bool", curr)
            return True

        if curr.lower() == 'false':
            logging.debug("Parsing '%s' as False bool", curr)
            return False

        logging.debug("Parsing '%s' as bare string", curr)

        return curr

    logging.debug("Parsing '%s' as operator...", curr)

    for op, num_args in OPS:
        if curr == op:
            logging.debug(op)
            retv = {}
            args = tuple( create_tree(tokens) for _ in range(num_args) )
            retv[op] = args

            return retv

    raise RuntimeError(f"Unable to parse '{curr}' (this should never happen).")


ARRAY_PATH_REGEX = re.compile(r'^(?P<path>[A-Za-z0-9]+)\[(?P<idx>\d+)?\]$')
def get_value(json: dict, prop_path: str):
    logging.debug("Getting value of '%s'", prop_path)

    curr = [json]
    for path_el in prop_path.split('.')[1:]:
        new_curr = []

        for el in curr:
            if m := ARRAY_PATH_REGEX.match(path_el):
                path = m['path']
                idx = m['idx']

                if path not in el:
                    logging.debug("Path '%s' not found - returning no value", path)
                    return None

                elif idx is None:
                    new_curr += el[path]

                else:
                    idx = int(idx)

                    if len(el[path]) < idx:
                        logging.debug("Index '%d' out of range (len=%d) - returning no value", idx, len(el[path]))
                        return None
                    else:
                        new_curr.append(el[path][idx])

            elif path_el not in el:
                logging.debug("Path '%s' not found - returning no value", path_el)
                return None

            else:
                new_curr.append(el[path_el])

            curr = new_curr

    if isinstance(curr, str):
        curr = curr

    if isinstance(curr, list):
        curr = [evaluate(json, el) for el in curr]

    logging.debug(curr)
    return curr


def some(callback, a=None, b=None) -> bool:
    try:
        if a is None:
            return _some_no_args(callback)
        elif b is None:
            return _some_one_arg(callback, a)
        else:
            return _some_two_arg(callback, a, b)

    except TypeError as te:
        return False


def _some_no_args(callback):
    return callback()


def _some_one_arg(callback, a):
    if not isinstance(a, list):
        a = [a]

    for x in a:
        if callback(x):
            return True

    return False


def _some_two_arg(callback, a, b):
    a_many = False
    b_many = False

    if isinstance(a, list):
        a_many = True

    if isinstance(b, list):
        b_many = True

    delegate_map = {
        (False, False): _some_one_to_one,
        (False, True): _some_one_to_many,
        (True, False): _some_many_to_one,
        (True, True): _some_many_to_many
    }

    some_del = delegate_map[(a_many, b_many)]
    return some_del(callback, a, b)


def _some_one_to_one(callback, a, b):
    return callback(a, b)


def _some_one_to_many(callback, a, b):
    for el in b:
        if callback(a, el):
            return True

    return False


def _some_many_to_one(callback, a, b):
    for el in a:
        if callback(el, b):
            return True

    return False


def _some_many_to_many(callback, a, b):
    for x, y in zip(a, b):
        if callback(x, y):
            return True

    return False


PATH_REGEX = re.compile(r'^(\.[A-Za-z0-9]+(\[\d*\])?)+$')
def evaluate(json: dict, operator):
    global comparer

    # A String operator should always be a property-path
    if isinstance(operator, str) and PATH_REGEX.search(operator) is not None:
            logging.debug("Evaluating '%s' as path", operator)

            value = get_value(json, operator)

            logging.debug(value)
            return value

    # These are parameters, and need to be eval'd/returned individually
    elif isinstance(operator, tuple):
        logging.debug("Evaluating %s as parameters", repr(operator))

        retv = tuple( evaluate(json, param) for param in operator )

        logging.debug(repr(retv))
        return retv

    # This is an actual operator
    if isinstance(operator, dict):
        logging.debug("Evaluating expression...")

        for op in operator:
            logging.debug("Evaluating '%s'", op)

            params = operator[op]

            if op == '-not':
                param_0 = evaluate(json, params[0])

                return some(lambda p: not p, param_0)

            if op == '-and':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return some(lambda a, b: a and b, param_0, param_1)

            if op == '-or':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return some(lambda a, b: a or b, param_0, param_1)

            if op == '-ex':
                param_0 = evaluate(json, params[0])

                return param_0 is not None

            if op == '-nex':
                param_0 = evaluate(json, params[0])

                return param_0 is None

            if op == '-in':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return some(lambda a, b: a in b, param_0, param_1)

            if op == '-nin':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return some(lambda a, b: a not in b, param_0, param_1)

            if op == '-eq':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return some(lambda a, b: comparer.compare(a, b) == 0, param_0, param_1)

            if op == '-ne':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return some(lambda a, b: comparer.compare(a, b) != 0, param_0, param_1)

            if op == '-mt' or op == '-rx':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                if param_0 is None:
                    return False

                if param_1 is None:
                    logging.critical("Invalid regular expression '%s'", params[1])
                    return False

                return some(lambda a, b: re.search(b, a) is not None, param_0, param_1)

            if op == '-lt':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return some(lambda a, b: comparer.compare(a, b) < 0, param_0, param_1)

            if op == '-le':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return some(lambda a, b: comparer.compare(a, b) <= 0, param_0, param_1)

            if op == '-gt':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return some(lambda a, b: comparer.compare(a, b) > 0, param_0, param_1)

            if op == '-ge':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return some(lambda a, b: comparer.compare(a, b) >= 0, param_0, param_1)

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

                return some(lambda p: isinstance(p, str), param_0)

            if op == '-num':
                param_0 = evaluate(json, params[0])

                return some(lambda p: isinstance(p, int) or isinstance(p, float), param_0)

            if op == '-bool':
                param_0 = evaluate(json, params[0])

                return some(lambda p: isinstance(p, bool), param_0)

    logging.debug("Evaluating '%s' as bare string", operator)
    return operator


def list_files(args):
    dir_path = args.root

    logging.info("Searching for files under '%s'", dir_path)

    for root, dirs, files in os.walk(dir_path):
        for f in files:
            logging.debug("Found '%s'", f)
            yield os.path.join(root, f)

        if not args.recurse:
            logging.debug("Halting recursive search")
            return


def set_logging_level(verbosity: int):
    if verbosity == 0:
        level = logging.WARNING
    elif verbosity == 1:
        level = logging.INFO
    else:
        level = logging.DEBUG

    logging.root.setLevel(level)


def main():
    global comparer

    args, token_list = get_args()

    set_logging_level(args.verbosity)
    if args.insensitive:
        comparer = InsensitiveComparer()

    token_queue = Queue(token_list)

    logging.info('Creating expression tree...')
    try:
        tree = create_tree(token_queue)
    except:
        logging.critical("Could not parse expression: %s", ' '.join(map(lambda t: f'"{t}"', token_list)))
        return

    valid_files = []
    for json_path in list_files(args):
        try:
            json_data = get_json(json_path)

        except:
            if json_path.endswith('.json'):
                logging.warn("Error parsing '%s' - skipping", json_path)
            else:
                logging.debug("Error parsing '%s' - skipping", json_path)

            continue

        retv = evaluate(json_data, tree)
        logging.debug("File '%s' evaluated to '%s'", json_path, retv)

        if not isinstance(retv, bool):
            raise TypeError(f"JQL does not resolve to a boolean (resolves to '{retv}')")

        if retv:
            valid_files.append(json_path)

    print(f"Files matching search criteria...")

    for vf in sorted(valid_files):
        print(f"{vf}")

    print(f"({len(valid_files)} files match)")


if __name__ == "__main__":
    main()
