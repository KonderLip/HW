import random
import time

import pytest

from solution import mergesort, quicksort, timed

# ============================================================
# Inputs for correctness tests
# ============================================================

INPUTS = [
    [],
    [1],
    [2, 1],
    [1, 2, 3],
    [3, 2, 1],
    [1, 1, 1],
    [3, 1, 2, 1, 3, 2],
    [-5, 3, -1, 0, 2],
    [5, -3, 0, 0, -3, 5],
    [42],
    list(range(100)),
    list(range(100, 0, -1)),
    [10**18, -(10**18), 0],
]


# ============================================================
# Correctness — mergesort
# ============================================================


@pytest.mark.parametrize("data", INPUTS)
def test_mergesort(data):
    assert mergesort(data) == sorted(data)


@pytest.mark.parametrize("seed", range(20))
def test_mergesort_random(seed):
    rng = random.Random(seed)
    n = rng.randint(0, 200)
    data = [rng.randint(-(10**6), 10**6) for _ in range(n)]
    assert mergesort(data) == sorted(data)


# ============================================================
# Correctness — quicksort
# ============================================================


@pytest.mark.parametrize("data", INPUTS)
def test_quicksort(data):
    assert quicksort(data, rng=random.Random(0)) == sorted(data)


@pytest.mark.parametrize("seed", range(20))
def test_quicksort_random(seed):
    rng = random.Random(seed)
    n = rng.randint(0, 200)
    data = [rng.randint(-(10**6), 10**6) for _ in range(n)]
    assert quicksort(data, rng=random.Random(seed)) == sorted(data)


def test_quicksort_deterministic():
    """Same rng seed -> same pivot sequence -> same internal operations."""
    data = [3, 1, 4, 1, 5, 9, 2, 6]
    a = quicksort(data, rng=random.Random(42))
    b = quicksort(data, rng=random.Random(42))
    assert a == b


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
    data = [3, 1, 2, 5, 4]
    snapshot = data.copy()
    sort_fn(data)
    assert data == snapshot


# ============================================================
# Mergesort stability
# ============================================================


class _K:
    """Comparable only by key, so we can detect unstable sorts."""

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

    def __repr__(self):
        return f"{self.key}:{self.tag}"


def test_mergesort_stable():
    data = [_K(1, "a"), _K(0, "b"), _K(1, "c"), _K(0, "d")]
    result = mergesort(data)
    assert [x.tag for x in result] == ["b", "d", "a", "c"]


# ============================================================
# timed decorator
# ============================================================


def test_timed_returns_result():
    @timed
    def add(a, b):
        return a + b

    assert add(2, 3) == 5


def test_timed_records_time():
    @timed
    def f():
        time.sleep(0.001)

    f()
    assert len(f.records) == 1
    assert f.records[0][0] == "f"
    assert f.records[0][1] >= 0.001


def test_timed_last():
    @timed
    def f():
        return 1

    assert f.last() is None
    f()
    first = f.last()
    time.sleep(0.001)
    f()
    assert f.last() > first


def test_timed_clear():
    @timed
    def f():
        return 1

    f()
    f()
    assert len(f.records) == 2
    f.clear()
    assert len(f.records) == 0
    assert f.last() is None


def test_timed_preserves_metadata():
    @timed
    def my_func():
        """docstring here"""
        return 42

    assert my_func.__name__ == "my_func"
    assert my_func.__doc__ == "docstring here"


def test_timed_records_on_exception():
    @timed
    def fail():
        raise ValueError("oops")

    with pytest.raises(ValueError):
        fail()
    # Even on exception, time is recorded (finally block)
    assert fail.last() is not None
    assert fail.last() >= 0


def test_timed_wraps_mergesort():
    t = timed(mergesort)
    assert t([3, 1, 2]) == [1, 2, 3]
    assert t.last() is not None


def test_timed_wraps_quicksort():
    t = timed(quicksort)
    assert t([3, 1, 2], rng=random.Random(0)) == [1, 2, 3]
    assert t.last() is not None


# ============================================================
# Benchmark helper
# ============================================================


def _bench(fn, data, repeats=3):
    """Run fn(data) `repeats` times after a warm-up; return the best (min) time.

    Using min instead of mean: the machine is noisy, and we want the fastest
    clean run, not the average polluted by GC pauses / scheduler hiccups.
    """
    fn(data)  # warm up: JIT caches, import caching, branch prediction
    best = float("inf")
    for _ in range(repeats):
        t = timed(fn)
        t(data)
        best = min(best, t.last())
    return best


def _quick_fn(seed=0):
    """Return a callable that runs quicksort with a fresh rng(seed)."""

    def fn(data):
        return quicksort(data, rng=random.Random(seed))

    fn.__name__ = "quicksort"
    return fn


# ============================================================
# Timing difference — where mergesort wins
# ============================================================


def test_mergesort_much_faster_on_sorted():
    """
    Sorted input triggers mergesort's short-circuit: `a[mid-1] <= a[mid]`
    holds at every split, so `_merge` is never called and the run is O(n).

    Quicksort with random pivot cannot detect sortedness, so it stays O(n log n).
    Expect mergesort to be at least 3x faster (in practice 10-30x).
    """
    n = 50_000
    data = list(range(n))

    t_merge = _bench(mergesort, data)
    t_quick = _bench(_quick_fn(), data)

    assert t_merge < t_quick / 3, (
        f"sorted input: expected mergesort >= 3x faster, "
        f"got merge={t_merge:.6f}s quick={t_quick:.6f}s"
    )


def test_mergesort_much_faster_on_all_equal():
    """
    All-equal input is also 'sorted' at every split: `a[mid-1] <= a[mid]`
    is trivially true, so mergesort short-circuits to O(n).

    Quicksort's Hoare partition does ~n/2 swaps at every recursion level
    (all of them no-ops value-wise, but real work), so it is O(n log n).
    """
    n = 50_000
    data = [42] * n

    t_merge = _bench(mergesort, data)
    t_quick = _bench(_quick_fn(), data)

    assert t_merge < t_quick / 2, (
        f"all-equal input: expected mergesort faster, "
        f"got merge={t_merge:.6f}s quick={t_quick:.6f}s"
    )


def test_mergesort_sorted_faster_than_random():
    """
    Direct evidence of the short-circuit: mergesort on sorted input must be
    significantly faster than on random input of the same size.
    """
    n = 30_000
    sorted_data = list(range(n))
    rng = random.Random(0)
    random_data = [rng.randint(0, n) for _ in range(n)]

    t_sorted = _bench(mergesort, sorted_data)
    t_random = _bench(mergesort, random_data)

    assert t_sorted < t_random / 2, (
        f"mergesort: sorted vs random should differ ~2x+, "
        f"got sorted={t_sorted:.6f}s random={t_random:.6f}s"
    )


# ============================================================
# Timing similarity — where they are comparable
# ============================================================


def test_similar_on_random(capsys):
    """
    On random input both are O(n log n) with similar constants.
    Neither should be more than 5x slower than the other.
    """
    n = 30_000
    rng = random.Random(0)
    data = [rng.randint(-(10**6), 10**6) for _ in range(n)]

    t_merge = _bench(mergesort, data)
    t_quick = _bench(_quick_fn(), data)

    with capsys.disabled():
        print(
            f"\n[random n={n}] merge={t_merge * 1000:.2f}ms "
            f"quick={t_quick * 1000:.2f}ms"
        )

    ratio = max(t_merge, t_quick) / max(min(t_merge, t_quick), 1e-9)
    assert ratio < 5, (
        f"random input: expected comparable, "
        f"got merge={t_merge:.6f}s quick={t_quick:.6f}s (ratio {ratio:.2f})"
    )


if __name__ == "__main__":
    pytest.main()
