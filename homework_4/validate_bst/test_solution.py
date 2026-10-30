import random
import sys

import pytest

from homework_4.tree import Node
from solution import main

sys.setrecursionlimit(10_000)


# ============================================================
# Oracle
# ============================================================


def is_bst_oracle(node: Node | None) -> bool:
    """Iterative in-order traversal; checks strictly increasing sequence.

    Conceptually independent of main(): main uses (lower, upper) range
    propagation, oracle uses the "in-order must be sorted" characterization.
    """
    stack = []
    keys = []
    cur = node
    while stack or cur is not None:
        while cur is not None:
            stack.append(cur)
            cur = cur.left
        cur = stack.pop()
        keys.append(cur.key)
        cur = cur.right
    for a, b in zip(keys, keys[1:]):
        if a >= b:
            return False
    return True


# ============================================================
# Builders / generators
# ============================================================


def collect(node: Node | None) -> list[Node]:
    if node is None:
        return []
    result = []
    stack = [node]
    while stack:
        n = stack.pop()
        result.append(n)
        if n.left is not None:
            stack.append(n.left)
        if n.right is not None:
            stack.append(n.right)
    return result


def gen_shape(rng: random.Random, n: int) -> Node | None:
    """Random tree shape with n nodes; keys are placeholders (0)."""
    if n == 0:
        return None
    nodes = [Node(0) for _ in range(n)]
    free = [nodes[0]]
    for i in range(1, n):
        node = nodes[i]
        idx = rng.randrange(len(free))
        parent = free[idx]
        if parent.left is None:
            parent.left = node
        else:
            parent.right = node
        if parent.left is not None and parent.right is not None:
            free[idx] = free[-1]
            free.pop()
        free.append(node)
    return nodes[0]


def assign_in_order(root: Node | None, start: int = 0) -> None:
    """Assign keys start, start+1, ... in in-order -> valid BST by construction."""
    counter = [start]

    def walk(n: Node | None) -> None:
        if n is None:
            return
        walk(n.left)
        n.key = counter[0]
        counter[0] += 1
        walk(n.right)

    walk(root)


def gen_valid_bst(rng: random.Random, n: int, start: int = 0) -> Node | None:
    root = gen_shape(rng, n)
    assign_in_order(root, start)
    return root


def gen_invalid_bst(rng: random.Random, n: int) -> Node:
    """Valid BST with two distinct keys swapped -> invalid BST."""
    if n < 2:
        raise ValueError("n must be >= 2")
    root = gen_valid_bst(rng, n)
    nodes = collect(root)
    i, j = rng.sample(range(n), 2)
    nodes[i].key, nodes[j].key = nodes[j].key, nodes[i].key
    return root


def gen_random_keys(
    rng: random.Random,
    n: int,
    lo: int = -100,
    hi: int = 100,
) -> Node | None:
    """Random shape with random keys — almost always invalid."""
    root = gen_shape(rng, n)
    for node in collect(root):
        node.key = rng.randint(lo, hi)
    return root


def make_left_chain_decreasing(n: int) -> Node | None:
    """n -> n-1 -> ... -> 1 via left pointers. Valid BST."""
    if n == 0:
        return None
    root = Node(n)
    cur = root
    for k in range(n - 1, 0, -1):
        cur.left = Node(k)
        cur = cur.left
    return root


def make_left_chain_increasing(n: int) -> Node | None:
    """1 -> 2 -> ... -> n via left pointers. Invalid BST."""
    if n == 0:
        return None
    root = Node(1)
    cur = root
    for k in range(2, n + 1):
        cur.left = Node(k)
        cur = cur.left
    return root


def make_right_chain_increasing(n: int) -> Node | None:
    """1 -> 2 -> ... -> n via right pointers. Valid BST."""
    if n == 0:
        return None
    root = Node(1)
    cur = root
    for k in range(2, n + 1):
        cur.right = Node(k)
        cur = cur.right
    return root


def make_right_chain_decreasing(n: int) -> Node | None:
    """n -> n-1 -> ... -> 1 via right pointers. Invalid BST."""
    if n == 0:
        return None
    root = Node(n)
    cur = root
    for k in range(n - 1, 0, -1):
        cur.right = Node(k)
        cur = cur.right
    return root


# ============================================================
# Manual cases
# ============================================================


def test_empty():
    assert main(None) is True


def test_single():
    assert main(Node(0)) is True


def test_two_valid_left():
    assert main(Node(2, Node(1))) is True


def test_two_valid_right():
    assert main(Node(1, None, Node(2))) is True


def test_two_invalid_left():
    assert main(Node(1, Node(2))) is False


def test_two_invalid_right():
    assert main(Node(2, None, Node(1))) is False


def test_perfect_3():
    assert main(Node(2, Node(1), Node(3))) is True


def test_duplicate_root_left():
    assert main(Node(2, Node(2), Node(3))) is False


def test_duplicate_root_right():
    assert main(Node(2, Node(1), Node(2))) is False


def test_duplicate_deep():
    """Duplicate not at root, but deeper."""
    root = Node(5, Node(3, Node(3)), Node(7))
    assert main(root) is False


def test_classic_invalid():
    """[5,1,4,null,null,3,6] — 4 is in right subtree of 5, but 4 < 5."""
    root = Node(5, Node(1), Node(4, Node(3), Node(6)))
    assert main(root) is False


def test_left_subtree_too_large():
    """Left subtree of root contains a value > root."""
    root = Node(5, Node(3, Node(2), Node(6)), Node(7))
    assert main(root) is False


def test_right_subtree_too_small():
    root = Node(5, Node(3), Node(7, Node(4), Node(8)))
    assert main(root) is False


def test_deep_left_in_right_subtree():
    """
    Root 5, right subtree 8 -> 7 -> 4 via left pointers.
    Every parent-child pair is locally consistent (4<7<8, 8>5),
    but 4 sits in the right subtree of 5 and must be > 5. Classic case
    where "only compare with direct children" fails.
    """
    root = Node(5, Node(3), Node(8, Node(7, Node(4)), None))
    assert main(root) is False


def test_deep_right_in_left_subtree():
    """Mirror of the above: 6 sits in left subtree of 5 but is > 5."""
    root = Node(5, Node(2, None, Node(3, None, Node(6))), Node(8))
    assert main(root) is False


def test_left_chain_valid():
    assert main(Node(3, Node(2, Node(1)))) is True


def test_right_chain_valid():
    assert main(Node(1, None, Node(2, None, Node(3)))) is True


def test_left_chain_invalid():
    assert main(Node(1, Node(2, Node(3)))) is False


def test_right_chain_invalid():
    assert main(Node(3, None, Node(2, None, Node(1)))) is False


def test_negatives_valid():
    root = Node(0, Node(-10, Node(-20), Node(-5)), Node(10))
    assert main(root) is True


def test_negatives_invalid():
    root = Node(0, Node(-10, Node(-20), Node(5)), Node(10))
    assert main(root) is False


def test_huge_values_valid():
    """float('inf') sentinels must work with very large ints."""
    root = Node(0, Node(-(10**18)), Node(10**18))
    assert main(root) is True


def test_huge_values_invalid():
    """Large positive value buried in the left subtree of 0."""
    root = Node(0, Node(-(10**18), Node(10**18 - 1)), Node(10**18))
    assert main(root) is False


def test_astronomically_large_values():
    """10**400 exceeds float max — Python int/float comparison stays exact."""
    root = Node(0, Node(-(10**400)), Node(10**400))
    assert main(root) is True


# ============================================================
# Random keys vs oracle
# ============================================================


@pytest.mark.parametrize("n", [0, 1, 2, 3, 5, 10, 20, 50, 100])
@pytest.mark.parametrize("seed", range(20))
def test_random_keys_vs_oracle(n, seed):
    rng = random.Random(seed)
    root = gen_random_keys(rng, n)
    assert main(root) == is_bst_oracle(root)


# ============================================================
# Valid BSTs -> must be True
# ============================================================


@pytest.mark.parametrize("n", [1, 2, 3, 5, 10, 20, 50, 100])
@pytest.mark.parametrize("start", [0, -50, 1000])
@pytest.mark.parametrize("seed", range(5))
def test_generated_valid_bst(n, start, seed):
    rng = random.Random(seed)
    root = gen_valid_bst(rng, n, start=start)
    # Sanity-check the generator itself, not just main().
    assert is_bst_oracle(root) is True
    assert main(root) is True


# ============================================================
# Invalid BSTs (swap) -> must be False
# ============================================================


@pytest.mark.parametrize("n", [2, 3, 5, 10, 20, 50, 100])
@pytest.mark.parametrize("seed", range(5))
def test_generated_invalid_bst(n, seed):
    rng = random.Random(seed)
    root = gen_invalid_bst(rng, n)
    assert is_bst_oracle(root) is False
    assert main(root) is False


# ============================================================
# Deep chains (500 nodes) — no recursion limit issues
# ============================================================


@pytest.mark.parametrize("n", [1, 2, 3, 10, 100, 500])
def test_left_chain_decreasing(n):
    root = make_left_chain_decreasing(n)
    assert main(root) is True
    assert main(root) == is_bst_oracle(root)


@pytest.mark.parametrize("n", [2, 3, 10, 100, 500])
def test_left_chain_increasing(n):
    root = make_left_chain_increasing(n)
    assert main(root) is False
    assert main(root) == is_bst_oracle(root)


@pytest.mark.parametrize("n", [1, 2, 3, 10, 100, 500])
def test_right_chain_increasing(n):
    root = make_right_chain_increasing(n)
    assert main(root) is True
    assert main(root) == is_bst_oracle(root)


@pytest.mark.parametrize("n", [2, 3, 10, 100, 500])
def test_right_chain_decreasing(n):
    root = make_right_chain_decreasing(n)
    assert main(root) is False
    assert main(root) == is_bst_oracle(root)


if __name__ == "__main__":
    pytest.main()
