import random
import sys

import pytest

from solution import mergesort, quicksort

# ============================================================
# Small manual cases
# ============================================================

MANUAL = [
    [],
    [1],
    [2, 1],
    [1, 2, 3],
    [3, 2, 1],
    [1, 1, 1],
    [3, 1, 2, 1, 3, 2],
    [-5, 3, -1, 0, 2],
    [5, -3, 0, 0, -3, 5],
    [10**18, -(10**18), 0],
]


@pytest.mark.parametrize("data", MANUAL)
def test_mergesort_manual(data):
    assert mergesort(data) == sorted(data)


@pytest.mark.parametrize("data", MANUAL)
def test_quicksort_manual(data):
    assert quicksort(data, rng=random.Random(0)) == sorted(data)


# ============================================================
# Exhaustive sizes 0..50
# ============================================================


@pytest.mark.parametrize("n", range(51))
def test_mergesort_all_sizes(n):
    rng = random.Random(n)
    data = [rng.randint(-1000, 1000) for _ in range(n)]
    assert mergesort(data) == sorted(data)


@pytest.mark.parametrize("n", range(51))
def test_quicksort_all_sizes(n):
    rng = random.Random(n)
    data = [rng.randint(-1000, 1000) for _ in range(n)]
    assert quicksort(data, rng=random.Random(n)) == sorted(data)


# ============================================================
# Mergesort: non-power-of-2 sizes (bottom-up quirk)
# ============================================================
#
# The while `width < n` loop must handle the last block cleanly when
# its size is smaller than `width`. Test sizes that are just below,
# just above, and just at powers of two.


@pytest.mark.parametrize(
    "n",
    [
        2, 3, 4, 5, 6, 7, 8, 9, 15, 16, 17,
        31, 32, 33, 63, 64, 65,
        127, 128, 129, 255, 256, 257,
        1000, 1023, 1024, 1025,
    ],
)
def test_mergesort_non_power_of_two(n):
    rng = random.Random(n)
    data = [rng.randint(-1000, 1000) for _ in range(n)]
    assert mergesort(data) == sorted(data)


# ============================================================
# Patterns
# ============================================================


@pytest.mark.parametrize("n", [1, 2, 3, 10, 100, 1000])
@pytest.mark.parametrize(
    "make",
    [
        lambda n: list(range(n)),
        lambda n: list(range(n, 0, -1)),
        lambda n: [42] * n,
        lambda n: [i % 3 for i in range(n)],
    ],
)
def test_patterns_both(n, make):
    data = make(n)
    assert mergesort(data) == sorted(data)
    assert quicksort(data, rng=random.Random(0)) == sorted(data)


# ============================================================
# Input is not mutated
# ============================================================


@pytest.mark.parametrize(
    "sort_fn",
    [
        mergesort,
        lambda d: quicksort(d, rng=random.Random(0)),
    ],
)
def test_input_not_mutated(sort_fn):
    data = [5, 2, 8, 1, 9, 3, 7, 4, 6, 0]
    snapshot = data.copy()
    sort_fn(data)
    assert data == snapshot


# ============================================================
# Mergesort stability
# ============================================================


class _K:
    __slots__ = ("key", "tag")

    def __init__(self, key, tag):
        self.key = key
        self.tag = tag

    def __lt__(self, other):
        return self.key < other.key

    def __le__(self, other):
        return self.key <= other.key

    def __eq__(self, other):
        return self.key == other.key


def test_mergesort_stable():
    data = [_K(1, "a"), _K(0, "b"), _K(1, "c"), _K(0, "d"), _K(1, "e")]
    result = mergesort(data)
    assert [x.tag for x in result] == ["b", "d", "a", "c", "e"]


# ============================================================
# Quicksort determinism with fixed rng
# ============================================================


def test_quicksort_deterministic():
    data = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
    a = quicksort(data, rng=random.Random(42))
    b = quicksort(data, rng=random.Random(42))
    assert a == b
    assert a == sorted(data)


# ============================================================
# Truly iterative: no Python recursion at all
# ============================================================
#
# Both wrappers use explicit stacks; only _merge / _partition are
# called, and both are iterative. If someone accidentally introduced
# recursion, the default Python limit (1000) would crash on n=10_000.


def test_no_recursion_mergesort():
    old = sys.getrecursionlimit()
    sys.setrecursionlimit(50)
    try:
        rng = random.Random(0)
        data = [rng.randint(-(10**6), 10**6) for _ in range(10_000)]
        assert mergesort(data) == sorted(data)
    finally:
        sys.setrecursionlimit(old)


def test_no_recursion_quicksort():
    old = sys.getrecursionlimit()
    sys.setrecursionlimit(50)
    try:
        rng = random.Random(0)
        data = [rng.randint(-(10**6), 10**6) for _ in range(10_000)]
        assert quicksort(data, rng=random.Random(0)) == sorted(data)
    finally:
        sys.setrecursionlimit(old)


# ============================================================
# Large n
# ============================================================


@pytest.mark.parametrize("n", [10_000, 100_000])
@pytest.mark.parametrize("pattern", ["random", "sorted", "reversed", "all_eq"])
def test_large(n, pattern):
    if pattern == "random":
        rng = random.Random(0)
        data = [rng.randint(-(10**9), 10**9) for _ in range(n)]
    elif pattern == "sorted":
        data = list(range(n))
    elif pattern == "reversed":
        data = list(range(n, 0, -1))
    else:
        data = [7] * n

    assert mergesort(data) == sorted(data)
    assert quicksort(data, rng=random.Random(0)) == sorted(data)


# ============================================================
# Adversarial pivot: quicksort must stay correct
# ============================================================
#
# _ExtremeRandom always returns the lower bound of randint, so
# _partition always picks the leftmost element as pivot. On sorted
# input this forces the worst-case split (1 vs n-1). The implementation
# uses smaller-half-first, so the stack still stays small — but the
# observable property from outside is just "still correct and terminates".


class _ExtremeRandom(random.Random):
    def randint(self, a, b):
        return a


@pytest.mark.parametrize("n", [1_000, 5_000])
@pytest.mark.parametrize("pattern", ["sorted", "reversed"])
def test_quicksort_adversarial_pivot(n, pattern):
    data = list(range(n)) if pattern == "sorted" else list(range(n, 0, -1))
    rng = _ExtremeRandom(0)
    assert quicksort(data, rng=rng) == sorted(data)


if __name__ == "__main__":
    pytest.main()
