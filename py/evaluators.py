class _Evaluator:
    def _evaluate(self, callback, a=None, b=None):
        raise NotImplementedError


class SomeEvaluator(_Evaluator):
    _instance = None

    def __init__(self):
        super().__init__()

        self.delegate_map = {
            (False, False): self._some_one_to_one,
            (False, True): self._some_one_to_many,
            (True, False): self._some_many_to_one,
            (True, True): self._some_many_to_many
        }

    @staticmethod
    def instance():
        if SomeEvaluator._instance is None:
            SomeEvaluator._instance = SomeEvaluator()
        return SomeEvaluator._instance

    @staticmethod
    def evaluate(callback, a=None, b=None):
        return SomeEvaluator.instance()._evaluate(callback, a, b)

    def _evaluate(self, callback, a=None, b=None) -> bool:
        try:
            if a is None:
                return self._some_no_args(callback)
            elif b is None:
                return self._some_one_arg(callback, a)
            else:
                return self._some_two_arg(callback, a, b)

        except TypeError as te:
            return False

    def _some_no_args(self, callback):
        return callback()

    def _some_one_arg(self, callback, a):
        if not isinstance(a, list):
            a = [a]

        for x in a:
            if callback(x):
                return True

        return False

    def _some_two_arg(self, callback, a, b):
        a_many = False
        b_many = False

        if isinstance(a, list):
            a_many = True

        if isinstance(b, list):
            b_many = True

        some_del = self.delegate_map[(a_many, b_many)]
        return some_del(callback, a, b)

    def _some_one_to_one(self, callback, a, b):
        return callback(a, b)

    def _some_one_to_many(self, callback, a, b):
        for el in b:
            if callback(a, el):
                return True

        return False

    def _some_many_to_one(self, callback, a, b):
        for el in a:
            if callback(el, b):
                return True

        return False

    def _some_many_to_many(self, callback, a, b):
        for x, y in zip(a, b):
            if callback(x, y):
                return True

        return False


class AllEvaluator(_Evaluator):
    _instance = None

    def __init__(self):
        super().__init__()

        self.delegate_map = {
            (False, False): self._all_one_to_one,
            (False, True): self._all_one_to_many,
            (True, False): self._all_many_to_one,
            (True, True): self._all_many_to_many
        }

    @staticmethod
    def instance():
        if AllEvaluator._instance is None:
            AllEvaluator._instance = AllEvaluator()
        return AllEvaluator._instance

    @staticmethod
    def evaluate(callback, a=None, b=None):
        return AllEvaluator.instance()._evaluate(callback, a, b)

    def _evaluate(self, callback, a=None, b=None) -> bool:
        try:
            if a is None:
                return self._all_no_args(callback)
            elif b is None:
                return self._all_one_arg(callback, a)
            else:
                return self._all_two_arg(callback, a, b)

        except TypeError as te:
            return False

    def _all_no_args(self, callback):
        return callback()

    def _all_one_arg(self, callback, a):
        if not isinstance(a, list):
            a = [a]

        for x in a:
            if callback(x):
                return True

        return False

    def _all_two_arg(self, callback, a, b):
        a_many = False
        b_many = False

        if isinstance(a, list):
            a_many = True

        if isinstance(b, list):
            b_many = True

        all_del = self.delegate_map[(a_many, b_many)]
        return all_del(callback, a, b)

    def _all_one_to_one(self, callback, a, b):
        return callback(a, b)

    def _all_one_to_many(self, callback, a, b):
        for el in b:
            if not callback(a, el):
                return False

        return True

    def _all_many_to_one(self, callback, a, b):
        for el in a:
            if not callback(el, b):
                return False

        return True

    def _all_many_to_many(self, callback, a, b):
        for x, y in zip(a, b):
            if not callback(x, y):
                return False

        return True
