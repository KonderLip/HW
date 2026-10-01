import random
from collections import Counter
from typing import List

import pytest

from solution import main


def oracle(words: List[str]) -> List[List[str]]:
    groups = []
    for word in words:
        word_counter = Counter(word)
        for group in groups:
            if Counter(group[0]) == word_counter:
                group.append(word)
                break
        else:
            groups.append([word])
    return groups


def normalize(groups: List[List[str]]) -> list:
    return sorted(sorted(g) for g in groups)


def gen(
    n: int,
    k: int,
    alphabet: str,
    max_len: int,
    rng: random.Random,
) -> List[str]:
    k = min(n, k)

    templates: List[str] = []
    for _ in range(k):
        length = rng.randint(0, max_len)
        letters = sorted(rng.choice(alphabet) for _ in range(length))
        templates.append("".join(letters))

    words: List[str] = []
    for _ in range(n):
        t = rng.choice(templates)
        letters = list(t)
        rng.shuffle(letters)
        words.append("".join(letters))

    rng.shuffle(words)
    return words


MANUAL_CASES = [
    (
        ["eat", "tea", "tan", "ate", "nat", "bat"],
        [["bat"], ["nat", "tan"], ["ate", "eat", "tea"]],
    ),
    ([], []),
    ([""], [[""]]),
    (["abc"], [["abc"]]),
    (["", "a", "", "b", ""], [["", "", ""], ["a"], ["b"]]),
    (["ab", "ba", "ab", "ba"], [["ab", "ba", "ab", "ba"]]),
    (["a", "b", "c"], [["a"], ["b"], ["c"]]),
    (
        ["abc", "bca", "cab", "xyz", "zyx", "q"],
        [["abc", "bca", "cab"], ["xyz", "zyx"], ["q"]],
    ),
    (["", "a", "aa", "a", ""], [["", ""], ["a", "a"], ["aa"]]),
]


@pytest.mark.parametrize("words, expected", MANUAL_CASES)
def test_manual(words, expected):
    assert normalize(main(words)) == normalize(expected)


@pytest.mark.parametrize("n", [0, 1, 2, 5, 20, 100, 500])
@pytest.mark.parametrize("k", [1, 2, 5, 10])
@pytest.mark.parametrize(
    "alphabet, max_len",
    [
        ("a", 10),
        ("ab", 5),
        ("abc", 4),
        ("abcdef", 3),
    ],
)
@pytest.mark.parametrize("seed", list(range(5)))
def test_generated(n, k, alphabet, max_len, seed):
    rng = random.Random(seed)

    if n == 0:
        words: List[str] = []
    else:
        words = gen(n, k, alphabet, max_len, rng)

    expected = oracle(words)
    actual = main(words)

    flat_actual = sorted(w for g in actual for w in g)
    assert flat_actual == sorted(words)

    assert normalize(actual) == normalize(expected)


@pytest.mark.parametrize("seed", list(range(200)))
def test_matches_counter_key(seed):
    rng = random.Random(seed)
    n = rng.randint(0, 50)
    words = gen(n, k=rng.randint(1, 5), alphabet="abcde", max_len=6, rng=rng)

    expected_groups = {}
    for w in words:
        expected_groups.setdefault(frozenset(Counter(w).items()), []).append(w)

    expected = list(expected_groups.values())
    assert normalize(main(words)) == normalize(expected)


if __name__ == "__main__":
    pytest.main()
