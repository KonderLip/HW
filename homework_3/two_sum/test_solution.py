import random
from typing import List

import pytest

from solution import main


def gen(n: int, k: int, low: int, high: int, rng: random.Random) -> List[int]:
    arr = []

    i, j = rng.sample(range(n), 2)
    a = rng.randint(max(low, k - high), min(high, k - low))
    b = k - a
    used = {k - a, k - b}

    for idx in range(n):
        if idx == i:
            arr.append(a)
        elif idx == j:
            arr.append(b)
        else:
            val = rng.randint(low, high)
            if val in used:
                for val in rng.sample(range(low, high + 1), high - low + 1):
                    if val not in used:
                        break
                else:
                    raise ValueError
            used.add(k - val)
            arr.append(val)

    return arr


MANUAL_CASES = [
    ([1, 3, 4, 10], 7, (1, 2)),
    ([5, 5, 1, 4], 10, (0, 1)),
    ([2, 3, 4], 6, (0, 2)),
    ([3, 4, 2], 6, (1, 2)),
    ([1, 2], 3, (0, 1)),
    ([0, 0], 0, (0, 1)),
    ([-1, 0, 1], 0, (0, 2)),
]


@pytest.mark.parametrize("arr, k, expected", MANUAL_CASES)
def test_manual(arr, k, expected):
    assert main(arr, k) == expected


def test_single_element_raises():
    with pytest.raises(ValueError):
        main([3], 6)


def test_no_pair_raises():
    with pytest.raises(ValueError):
        main([1, 2, 3], 100)


@pytest.mark.parametrize("n", [10, 100, 1_000, 10_000])
@pytest.mark.parametrize(
    "low, high",
    [
        (-10, 10),
        (-100, 100),
        (-1_000, 1_000),
        (0, 2_000),
        (-2_000, 0),
        (-10_000, 10_000),
    ],
)
@pytest.mark.parametrize("seed", list(range(5)))
def test_generated(n, low, high, seed):
    rng = random.Random(seed)

    k = rng.randint(2 * low, 2 * high)

    try:
        arr = gen(n, k, low, high, rng)
    except ValueError:
        pytest.skip()

    i, j = main(arr, k)
    assert i < j
    assert arr[i] + arr[j] == k


if __name__ == "__main__":
    pytest.main()
