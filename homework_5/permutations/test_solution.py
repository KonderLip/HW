import itertools
import math
import random

import pytest

from solution import main


@pytest.fixture(autouse=True)
def _silence_tracer(capsys):
    """tracer prints on every recursive call; discard between tests."""
    yield
    capsys.readouterr()


# ============================================================
# Manual examples (from the spec)
# ============================================================


def test_example_1():
    assert main([1, 2, 3]) == [
        [1, 2, 3],
        [1, 3, 2],
        [2, 1, 3],
        [2, 3, 1],
        [3, 1, 2],
        [3, 2, 1],
    ]


def test_example_2():
    assert main([0, 1]) == [[0, 1], [1, 0]]


def test_example_3():
    assert main([1]) == [[1]]


# ============================================================
# Edge cases
# ============================================================


def test_empty():
    # Mathematically the empty set has exactly one permutation: itself.
    # This matches itertools.permutations([]) == [()].
    assert main([]) == [[]]


def test_two_elements():
    assert set(map(tuple, main([1, 2]))) == {(1, 2), (2, 1)}


def test_negative_numbers():
    result = main([-1, -2])
    assert set(map(tuple, result)) == {(-1, -2), (-2, -1)}


def test_large_values():
    result = main([10**18, -(10**18)])
    assert set(map(tuple, result)) == {
        (10**18, -(10**18)),
        (-(10**18), 10**18),
    }


# ============================================================
# Count: exactly n! results
# ============================================================


@pytest.mark.parametrize("n", range(0, 7))
def test_count_is_factorial(n):
    nums = list(range(n))
    assert len(main(nums)) == math.factorial(n)


# ============================================================
# Uniqueness: no duplicates in output
# ============================================================


@pytest.mark.parametrize("n", range(0, 7))
def test_no_duplicates(n):
    nums = list(range(n))
    result = main(nums)
    assert len(set(map(tuple, result))) == len(result)


# ============================================================
# Each element is a valid permutation of the input
# ============================================================


@pytest.mark.parametrize("n", range(1, 6))
def test_each_is_a_permutation(n):
    nums = list(range(n))
    for perm in main(nums):
        assert sorted(perm) == sorted(nums)


# ============================================================
# Oracle: set equality with itertools.permutations
# ============================================================


@pytest.mark.parametrize(
    "nums",
    [
        [1, 2, 3],
        [0, 1],
        [1],
        [],
        [5, -3, 0, 7],
        [-1, -2, -3],
        [42, 17, 99, 0, -5],
    ],
)
def test_matches_itertools(nums):
    expected = {tuple(p) for p in itertools.permutations(nums)}
    actual = {tuple(p) for p in main(nums)}
    assert actual == expected


# ============================================================
# Random inputs vs oracle
# ============================================================


@pytest.mark.parametrize("seed", range(15))
def test_random_vs_oracle(seed):
    rng = random.Random(seed)
    n = rng.randint(0, 5)
    nums = rng.sample(range(-1000, 1000), n)

    expected = {tuple(p) for p in itertools.permutations(nums)}
    actual = {tuple(p) for p in main(nums)}
    assert actual == expected


# ============================================================
# Result independence: permutations are copies, not shared refs
# ============================================================


def test_permutations_are_independent():
    result = main([1, 2, 3])
    # Mutating one permutation must not affect the others.
    result[0][0] = 999
    for perm in result[1:]:
        assert 999 not in perm


def test_result_elements_are_distinct_objects():
    result = main([1, 2, 3])
    ids = {id(p) for p in result}
    assert len(ids) == len(result)


# ============================================================
# Input immutability
# ============================================================


def test_input_not_mutated():
    nums = [1, 2, 3]
    main(nums)
    assert nums == [1, 2, 3]


def test_input_not_mutated_random():
    rng = random.Random(42)
    for _ in range(10):
        nums = rng.sample(range(-100, 100), rng.randint(1, 5))
        snapshot = nums.copy()
        main(nums)
        assert nums == snapshot


# ============================================================
# Consecutive calls do not leak state
# ============================================================


def test_consecutive_calls_independent():
    first = main([1, 2])
    second = main([3, 4, 5])
    assert len(first) == 2
    assert len(second) == 6
    # the second call's results must not contain anything from the first
    flat_second = {x for perm in second for x in perm}
    assert flat_second == {3, 4, 5}


# ============================================================
# Tracer is actually invoked
# ============================================================


def test_tracer_prints(capsys):
    main([1, 2])
    out = capsys.readouterr().out
    assert "->" in out
    assert "<-" in out
    assert "backtrack" in out


def test_tracer_top_level_has_no_indent(capsys):
    """The outermost call is at depth 0 — no leading spaces."""
    main([1, 2, 3])
    out = capsys.readouterr().out
    lines = out.split("\n")
    top_entries = [l for l in lines if l.startswith("-> backtrack")]
    assert len(top_entries) == 1


def test_tracer_depth_matches_recursion(capsys):
    """
    For n=3, recursion visits path lengths 0, 1, 2, 3.
    The depth-3 call is the base case (len(path) == n).
    With indent="  " the deepest line has 2 * 3 = 6 spaces.
    """
    main([1, 2, 3])
    out = capsys.readouterr().out
    max_indent = max(len(l) - len(l.lstrip()) for l in out.split("\n") if l)
    assert max_indent == 6


# ============================================================
# Documented behavior: duplicate values in input
# ============================================================


def test_duplicate_values_produce_index_level_permutations():
    """
    The implementation walks by *index*, not by value.
    For [1, 1, 2] it yields 3! = 6 entries, of which 3 are distinct
    by value. The spec does not mention duplicates; this test documents
    current behavior so a future fix (if desired) is a deliberate change.
    """
    result = main([1, 1, 2])
    assert len(result) == 6  # by position
    assert len(set(map(tuple, result))) == 3  # by value


if __name__ == "__main__":
    pytest.main()
