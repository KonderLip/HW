import random

import pytest

from solution import main

# ============================================================
# Oracle
# ============================================================
#
# The oracle is *not* the point of the exercise — the point is quickselect.
# Using sorted() here is fine: it's a reference, not the implementation.
# If someone replaces main() with sorted(nums)[n-k] the timing test below
# would still pass, but that's exactly why we shouldn't time in correctness
# tests, only assert equality.


def oracle(nums, k):
    return sorted(nums)[len(nums) - k]


# ============================================================
# Examples from the statement
# ============================================================


def test_example_1():
    assert main([3, 2, 1, 5, 6, 4], 2, rng=random.Random(0)) == 5


def test_example_2():
    assert main([3, 2, 3, 1, 2, 4, 5, 5, 6], 4, rng=random.Random(0)) == 4


# ============================================================
# Edge positions: k=1 (max), k=n (min), single element
# ============================================================


def test_k_equals_1_is_max():
    assert main([3, 1, 4, 1, 5, 9, 2, 6], 1, rng=random.Random(0)) == 9


def test_k_equals_n_is_min():
    assert main([3, 1, 4, 1, 5, 9, 2, 6], 8, rng=random.Random(0)) == 1


def test_single_element_k1():
    assert main([42], 1, rng=random.Random(0)) == 42


def test_two_elements():
    assert main([2, 1], 1, rng=random.Random(0)) == 2
    assert main([2, 1], 2, rng=random.Random(0)) == 1


# ============================================================
# Invalid k
# ============================================================


@pytest.mark.parametrize(
    "nums, k",
    [
        ([], 1),  # empty list, any k invalid
        ([1, 2, 3], 0),  # k < 1
        ([1, 2, 3], -1),
        ([1, 2, 3], 4),  # k > n
        ([1], 2),
    ],
)
def test_invalid_k_raises(nums, k):
    with pytest.raises(ValueError):
        main(nums, k)


# ============================================================
# Input is not mutated
# ============================================================


def test_input_not_mutated():
    data = [3, 1, 4, 1, 5, 9, 2, 6]
    snapshot = data.copy()
    main(data, 3, rng=random.Random(0))
    assert data == snapshot


def test_input_not_mutated_random():
    rng = random.Random(42)
    for _ in range(20):
        data = [rng.randint(-100, 100) for _ in range(rng.randint(1, 30))]
        snapshot = data.copy()
        main(data, rng.randint(1, len(data)), rng=random.Random(0))
        assert data == snapshot


# ============================================================
# Duplicates — this is what the 3-way partition is for
# ============================================================


def test_all_equal():
    assert main([7] * 100, 1, rng=random.Random(0)) == 7
    assert main([7] * 100, 50, rng=random.Random(0)) == 7
    assert main([7] * 100, 100, rng=random.Random(0)) == 7


def test_few_unique():
    data = [1, 2, 3] * 1000  # 3000 elements, 3 unique values
    for k in [1, 2, 3, 4, 1000, 1500, 2000, 2999, 3000]:
        assert main(data, k, rng=random.Random(0)) == oracle(data, k)


def test_all_equal_large():
    """O(n) expected for 3-way on constant array — no recursion blowup."""
    n = 100_000
    assert main([5] * n, 1, rng=random.Random(0)) == 5
    assert main([5] * n, n // 2, rng=random.Random(0)) == 5
    assert main([5] * n, n, rng=random.Random(0)) == 5


def test_duplicates_at_boundaries():
    """Duplicates around the k-th position — the classic Lomuto killer."""
    data = [1, 1, 1, 2, 2, 2, 2, 3, 3]
    for k in range(1, len(data) + 1):
        assert main(data, k, rng=random.Random(0)) == oracle(data, k)


# ============================================================
# Random inputs vs oracle
# ============================================================


@pytest.mark.parametrize("n", [1, 2, 3, 5, 10, 50, 200])
@pytest.mark.parametrize("seed", range(10))
def test_random_vs_oracle(n, seed):
    rng = random.Random(seed)
    data = [rng.randint(-1000, 1000) for _ in range(n)]
    for k in range(1, n + 1):
        assert main(data, k, rng=random.Random(seed)) == oracle(data, k)


@pytest.mark.parametrize("seed", range(20))
def test_random_specific_k(seed):
    rng = random.Random(seed)
    n = rng.randint(1, 500)
    data = [rng.randint(-(10**6), 10**6) for _ in range(n)]
    k = rng.randint(1, n)
    assert main(data, k, rng=random.Random(seed)) == oracle(data, k)


@pytest.mark.parametrize("pattern", ["sorted", "reversed"])
@pytest.mark.parametrize("seed", range(5))
def test_monotone_patterns(pattern, seed):
    """Monotone inputs are the classic O(n^2) trigger for naive quicksort."""
    n = 500
    data = list(range(n)) if pattern == "sorted" else list(range(n, 0, -1))
    for k in [1, n // 4, n // 2, 3 * n // 4, n]:
        assert main(data, k, rng=random.Random(seed)) == oracle(data, k)


# ============================================================
# Range of values: negatives, big ints
# ============================================================


def test_negatives():
    data = [-5, -1, -10, 0, 3, -3]
    for k in range(1, len(data) + 1):
        assert main(data, k, rng=random.Random(0)) == oracle(data, k)


def test_big_integers():
    data = [10**18, -(10**18), 0, 10**18 - 1, -(10**18) + 1]
    for k in range(1, len(data) + 1):
        assert main(data, k, rng=random.Random(0)) == oracle(data, k)


# ============================================================
# Determinism with fixed rng
# ============================================================


def test_deterministic_with_seed():
    data = [rng.randint(0, 100) for rng in [random.Random(1)] for _ in range(50)]
    a = main(data, 17, rng=random.Random(42))
    b = main(data, 17, rng=random.Random(42))
    assert a == b


# ============================================================
# Adversarial pivot: leftmost always
# ============================================================
#
# Force rng.randint to return its lower bound, so the pivot is always
# arr[lo]. On sorted input this gives the worst-case split for 2-way
# partitions. Our 3-way partition still has to *return the correct value*,
# even if slower.


class _LeftmostRandom(random.Random):
    def randint(self, a, b):
        return a


@pytest.mark.parametrize("n", [100, 500, 2000])
@pytest.mark.parametrize("pattern", ["sorted", "reversed"])
def test_adversarial_pivot_correctness(n, pattern):
    data = list(range(n)) if pattern == "sorted" else list(range(n, 0, -1))
    for k in [1, n // 2, n]:
        assert main(data, k, rng=_LeftmostRandom(0)) == oracle(data, k)


# ============================================================
# Large n — sanity, not a benchmark
# ============================================================


@pytest.mark.parametrize("n", [10_000, 100_000])
def test_large_random(n):
    rng = random.Random(0)
    data = [rng.randint(-(10**9), 10**9) for _ in range(n)]
    for k in [1, n // 4, n // 2, 3 * n // 4, n]:
        assert main(data, k, rng=random.Random(0)) == oracle(data, k)


@pytest.mark.parametrize("n", [10_000, 100_000])
def test_large_all_equal(n):
    """Must be fast thanks to 3-way partition — O(n), one pass."""
    data = [42] * n
    for k in [1, n // 2, n]:
        assert main(data, k, rng=random.Random(0)) == 42


@pytest.mark.parametrize("n", [10_000, 100_000])
def test_large_two_unique(n):
    """~50/50 split of two values — also a Lomuto-killer, 3-way handles it."""
    rng = random.Random(0)
    data = [rng.randint(0, 1) for _ in range(n)]
    for k in [1, n // 4, n // 2, 3 * n // 4, n]:
        assert main(data, k, rng=random.Random(0)) == oracle(data, k)


if __name__ == "__main__":
    pytest.main()
