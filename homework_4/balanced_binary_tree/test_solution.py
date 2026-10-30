import random
import sys

import pytest

from homework_4.tree import Node
from solution import main

# Naive oracle is recursive; raise the limit so deep trees don't blow up.
sys.setrecursionlimit(10_000)


# ---------------------------------------------------------- Naive oracle


def height(node: Node | None) -> int:
    """Recursive height: 0 for empty, 1 for a leaf."""
    if node is None:
        return 0
    return 1 + max(height(node.left), height(node.right))


def is_balanced_naive(node: Node | None) -> bool:
    """O(n^2) reference: recompute heights at every node."""
    if node is None:
        return True
    if abs(height(node.left) - height(node.right)) > 1:
        return False
    return is_balanced_naive(node.left) and is_balanced_naive(node.right)


# ------------------------------------------------------------ Builders


def make_perfect(h: int) -> Node | None:
    """Perfect binary tree of height h (2^h - 1 nodes)."""
    counter = [0]

    def build(level: int) -> Node | None:
        if level == 0:
            return None
        node = Node(counter[0])
        counter[0] += 1
        node.left = build(level - 1)
        node.right = build(level - 1)
        return node

    return build(h)


def make_line_left(n: int) -> Node | None:
    """Left-only path of n nodes."""
    if n == 0:
        return None
    root = Node(0)
    cur = root
    for i in range(1, n):
        cur.left = Node(i)
        cur = cur.left
    return root


def make_line_right(n: int) -> Node | None:
    if n == 0:
        return None
    root = Node(0)
    cur = root
    for i in range(1, n):
        cur.right = Node(i)
        cur = cur.right
    return root


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


# --------------------------------------------------------- Generators


def gen_random(rng: random.Random, n: int) -> Node | None:
    """Random tree of n nodes, shapes uniformly-ish."""
    if n == 0:
        return None
    nodes = [Node(i) for i in range(n)]
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
            # O(1) removal: swap with last, pop.
            free[idx] = free[-1]
            free.pop()
        free.append(node)
    return nodes[0]


def gen_balanced(rng: random.Random, h: int) -> Node | None:
    """Random balanced tree of exactly height h."""
    counter = [0]

    def build(level: int) -> Node | None:
        if level == 0:
            return None
        if level == 1:
            pairs = [(0, 0)]
        else:
            pairs = [
                (level - 1, level - 1),
                (level - 1, level - 2),
                (level - 2, level - 1),
            ]
        lh, rh = rng.choice(pairs)
        node = Node(counter[0])
        counter[0] += 1
        node.left = build(lh)
        node.right = build(rh)
        return node

    return build(h)


def perturb(rng: random.Random, root: Node, extra: int) -> None:
    """Attach a left-going chain of length `extra` to a random leaf."""
    leaves = [n for n in collect(root) if n.left is None and n.right is None]
    if not leaves:
        return
    cur = rng.choice(leaves)
    for i in range(extra):
        cur.left = Node(-1 - i)
        cur = cur.left


# ------------------------------------------------------ Manual cases


def test_empty():
    assert main(None) is True


def test_single():
    assert main(Node(0)) is True


def test_perfect_1():
    assert main(make_perfect(1)) is True


def test_perfect_3():
    assert main(make_perfect(3)) is True


def test_perfect_7():
    assert main(make_perfect(7)) is True


def test_left_line_2():
    """Root + left child: heights 1 and 0 -> diff 1 -> balanced."""
    assert main(make_line_left(2)) is True


def test_left_line_3():
    """Heights 2 and 0 at root -> unbalanced."""
    assert main(make_line_left(3)) is False


def test_right_line_3():
    assert main(make_line_right(3)) is False


def test_unbalanced_by_two_at_root():
    """Left subtree height 2, right height 0."""
    root = Node(0, Node(1, Node(2)), None)
    assert main(root) is False


def test_root_balanced_but_child_unbalanced():
    """
    At root: left height 3, right height 3 -> root OK.
    At left child: left height 2, right height 0 -> unbalanced deeper.
    """
    root = Node(
        1,
        Node(2, Node(3, Node(4)), None),
        Node(2, None, Node(3, None, Node(4))),
    )
    assert main(root) is False


def test_example_1():
    """[3,9,20,null,null,15,7] -> True"""
    root = Node(3, Node(9), Node(20, Node(15), Node(7)))
    assert main(root) is True


def test_example_2():
    """[1,2,2,3,3,null,null,4,4] -> False"""
    root = Node(
        1,
        Node(2, Node(3, Node(4), Node(4)), Node(3)),
        Node(2),
    )
    assert main(root) is False


# ------------------------------------------ Random vs naive oracle


@pytest.mark.parametrize("n", [0, 1, 2, 3, 5, 10, 20, 50, 100])
@pytest.mark.parametrize("seed", range(20))
def test_random_vs_oracle(n, seed):
    rng = random.Random(seed)
    root = gen_random(rng, n)
    assert main(root) == is_balanced_naive(root)


# ----------------------------------- Generated balanced trees -> True


@pytest.mark.parametrize("h", range(0, 10))
@pytest.mark.parametrize("seed", range(10))
def test_generated_balanced_is_true(h, seed):
    rng = random.Random(seed)
    root = gen_balanced(rng, h)
    # Sanity-check the generator itself, not just main().
    assert height(root) == h
    assert is_balanced_naive(root) is True
    assert main(root) is True


# ------------------- Perturbed balanced trees vs naive oracle


@pytest.mark.parametrize("h", [1, 2, 3, 4, 5])
@pytest.mark.parametrize("extra", [1, 2, 3])
@pytest.mark.parametrize("seed", range(10))
def test_perturbed_vs_oracle(h, extra, seed):
    """Balanced tree + deep chain. Expected outcome left to the oracle."""
    rng = random.Random(seed)
    root = gen_balanced(rng, h)
    perturb(rng, root, extra)
    assert main(root) == is_balanced_naive(root)


# -------------------------------------------- Path (line) trees


@pytest.mark.parametrize("n", [1, 2, 3, 5, 10, 50, 100, 500])
def test_left_line(n):
    root = make_line_left(n)
    # Line of length 1 or 2 is trivially balanced, >= 3 is not.
    expected = n <= 2
    assert main(root) is expected
    assert main(root) == is_balanced_naive(root)


@pytest.mark.parametrize("n", [1, 2, 3, 5, 10, 50, 100, 500])
def test_right_line(n):
    root = make_line_right(n)
    expected = n <= 2
    assert main(root) is expected
    assert main(root) == is_balanced_naive(root)


if __name__ == "__main__":
    pytest.main()
