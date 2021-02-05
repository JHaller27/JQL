class Comparer:
    def compare(self, a, b) -> int:
        if a < b:
            return -1
        elif a > b:
            return 1
        else:
            return 0


class _ComparerDecorator(Comparer):
    def __init__(self, base: Comparer):
        self._base = base

    @property
    def base(self) -> Comparer:
        return self._base

    def compare(self, a, b):
        return self._base.compare(a, b)


class InsensitiveComparer(_ComparerDecorator):
    def compare(self, a, b) -> int:
        if isinstance(a, str):
            a = a.lower()
        if isinstance(b, str):
            b = b.lower()

        return self.base.compare(a, b)


class ForceStringComparer(_ComparerDecorator):
    def compare(self, a, b):
        a = str(a)
        b = str(b)

        return self.base.compare(a, b)
