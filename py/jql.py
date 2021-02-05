import re
import os
import sys
import json
import shlex
import logging
import argparse
from evaluators import SomeEvaluator as Some
from evaluators import AllEvaluator as All
from comparers import *


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


comparer = Comparer()


def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('root', type=str, help='Path to root to search for .json files')
    parser.add_argument('--recurse', action='store_true', help='Recursively search for files')
    parser.add_argument('--insensitive', action='store_true', help='Compare strings as case-insensitive (does not affect JSON paths)')
    parser.add_argument('--string', dest='force_string', action='store_true', help='Compare all values as strings')
    parser.add_argument('--list', action='store_true', help='Skip all meta output and only list files')
    parser.add_argument('-v', dest='verbosity', action='count', default=0, help='Increase level of logging (default: none)')

    args, jql_tokens = parser.parse_known_args()

    if len(jql_tokens) == 0:
        raw_in = input("JQL expression> ")
        jql_tokens = shlex.split(raw_in)

    set_logging_level(args.verbosity)

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


BACKREF_REGEX = re.compile(r'\$(?P<refid>\d+)')


def create_tree(tokens: Queue, force_string=False, leaves=[]) -> dict:
    logging.debug("Creating expression tree from '%s'...", tokens.peek())

    # Key = op
    # Value = dict/tuple
    curr = tokens.pop()

    if curr.lower() not in ALL_OPS:
        try:
            val = int(curr)
            logging.debug("Parsing '%s' as int", curr)
            leaves.append(val)
            return val
        except ValueError:
            pass

        try:
            val = float(curr)
            logging.debug("Parsing '%s' as float", curr)
            leaves.append(val)
            return val
        except ValueError:
            pass

        if curr.lower() == 'true':
            logging.debug("Parsing '%s' as True bool", curr)
            val = True
            leaves.append(val)
            return val

        if curr.lower() == 'false':
            logging.debug("Parsing '%s' as False bool", curr)
            val = False
            leaves.append(val)
            return val

        if m := BACKREF_REGEX.match(curr):
            idx = int(m['refid'])
            if idx <= len(leaves):
                logging.debug("Parsing '%s' as back-reference", curr)
                return leaves[idx - 1]

        logging.debug("Parsing '%s' as bare string", curr)

        leaves.append(curr)
        return curr

    logging.debug("Parsing '%s' as operator...", curr)

    for op, num_args in OPS:
        if curr.lower() == op:
            logging.debug(curr)
            retv = {}
            args = tuple( create_tree(tokens, leaves) for _ in range(num_args) )
            retv[curr] = args

            return retv

    raise RuntimeError(f"Unable to parse '{curr}' (this should never happen).")


ARRAY_PATH_REGEX = re.compile(r'^(?P<path>[A-Za-z0-9]+)\[(?P<idx>\d+)?\]$')
def get_value(json: dict, prop_path: str):
    logging.debug("Getting value of '%s'", prop_path)

    curr = [json]
    for path_el in prop_path.split('.')[1:]:
        new_curr = []

        for el in curr:
            if el is None:
                continue

            elif m := ARRAY_PATH_REGEX.match(path_el):
                path = m['path']
                idx = m['idx']

                if path not in el:
                    logging.debug("Path '%s' not found - returning no value", path)
                    return None

                elif idx is None:
                    new_curr += el[path]

                else:
                    idx = int(idx)

                    if len(el[path]) <= idx:
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
        for op in operator:
            if not op.startswith('-'):
                break

            logging.debug("Evaluating expression '%s'", op)

            lop = op.lower()

            if op.islower():
                evaluator = Some
            elif op.isupper():
                evaluator = All
            else:
                logging.critical('Operator %s is of mixed case - cannot evaluate', op)

            params = operator[op]

            if lop == '-not':
                param_0 = evaluate(json, params[0])

                return evaluator.evaluate(lambda p: not p, param_0)

            if lop == '-and':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return evaluator.evaluate(lambda a, b: a and b, param_0, param_1)

            if lop == '-or':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return evaluator.evaluate(lambda a, b: a or b, param_0, param_1)

            if lop == '-ex':
                param_0 = evaluate(json, params[0])

                return param_0 is not None

            if lop == '-nex':
                param_0 = evaluate(json, params[0])

                return param_0 is None

            if lop == '-in':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return evaluator.evaluate(lambda a, b: a in b, param_0, param_1)

            if lop == '-nin':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return evaluator.evaluate(lambda a, b: a not in b, param_0, param_1)

            if lop == '-eq':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return evaluator.evaluate(lambda a, b: comparer.compare(a, b) == 0, param_0, param_1)

            if lop == '-ne':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return evaluator.evaluate(lambda a, b: comparer.compare(a, b) != 0, param_0, param_1)

            if lop == '-mt' or lop == '-rx':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                if param_0 is None:
                    return False

                if param_1 is None:
                    logging.critical("Invalid regular expression '%s'", params[1])
                    return False

                return evaluator.evaluate(lambda a, b: re.search(b, a) is not None, param_0, param_1)

            if lop == '-lt':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return evaluator.evaluate(lambda a, b: comparer.compare(a, b) < 0, param_0, param_1)

            if lop == '-le':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return evaluator.evaluate(lambda a, b: comparer.compare(a, b) <= 0, param_0, param_1)

            if lop == '-gt':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return evaluator.evaluate(lambda a, b: comparer.compare(a, b) > 0, param_0, param_1)

            if lop == '-ge':
                param_0 = evaluate(json, params[0])
                param_1 = evaluate(json, params[1])

                return evaluator.evaluate(lambda a, b: comparer.compare(a, b) >= 0, param_0, param_1)

            if lop == '-len':
                param_0 = evaluate(json, params[0])

                return len(param_0)

            if lop == '-obj':
                param_0 = evaluate(json, params[0])

                return evaluator.evaluate(lambda p: isinstance(p, dict), param_0)

            if lop == '-arr':
                param_0 = evaluate(json, params[0])

                return evaluator.evaluate(lambda p: isinstance(p, list), param_0)

            if lop == '-str':
                param_0 = evaluate(json, params[0])

                return evaluator.evaluate(lambda p: isinstance(p, str), param_0)

            if lop == '-num':
                param_0 = evaluate(json, params[0])

                return evaluator.evaluate(lambda p: isinstance(p, int) or isinstance(p, float), param_0)

            if lop == '-bool':
                param_0 = evaluate(json, params[0])

                return evaluator.evaluate(lambda p: isinstance(p, bool), param_0)

    logging.debug("Evaluating '%s' as primitive %s", operator, type(operator).__name__)
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


def sort_files(files):
    return sorted(files, key=lambda file: (os.path.dirname(file), os.path.basename(file)))


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

    logging.info(args)

    if args.insensitive:
        comparer = InsensitiveComparer(comparer)

    if args.force_string:
        comparer = ForceStringComparer(comparer)

    token_queue = Queue(token_list)

    logging.info('Creating expression tree...')
    try:
        tree = create_tree(token_queue, args.force_string)
    except:
        logging.critical("Could not parse expression: %s", ' '.join(map(lambda t: f'"{t}"', token_list)))
        return

    count_all_files = 0
    valid_files = []
    for json_path in list_files(args):
        try:
            json_data = get_json(json_path)

        except:
            if json_path.endswith('.json'):
                logging.info("Error parsing '%s' - skipping", json_path)
            else:
                logging.debug("Error parsing '%s' - skipping", json_path)

            continue

        count_all_files += 1

        retv = evaluate(json_data, tree)
        logging.debug("File '%s' evaluated to '%s'", json_path, retv)

        if not isinstance(retv, bool):
            raise TypeError(f"JQL does not resolve to a boolean (resolves to '{retv}')")

        if retv:
            valid_files.append(json_path)

    if not args.list:
        print(f"Files matching search criteria...")

    for vf in sort_files(valid_files):
        print(f"{vf}")

    if not args.list:
        print(f"({len(valid_files)}/{count_all_files} files match)")


if __name__ == "__main__":
    main()
