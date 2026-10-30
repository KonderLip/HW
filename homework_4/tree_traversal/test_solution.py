import random
import sys

import pytest

from homework_4.tree import Node
from homework_4.validate_bst.solution import main as validate_bst
from solution import (
    BST,
    traverse,
    preorder,
    inorder,
    postorder,
    reverse_preorder,
    reverse_inorder,
    reverse_postorder,
)

sys.setrecursionlimit(10_000)


# ============================================================
# Oracles: independent recursive implementations
# ============================================================


def preorder_rec(node):
    if node is None:
        return []
    return [node.key] + preorder_rec(node.left) + preorder_rec(node.right)


def inorder_rec(node):
    if node is None:
        return []
    return inorder_rec(node.left) + [node.key] + inorder_rec(node.right)


def postorder_rec(node):
    if node is None:
        return []
    return postorder_rec(node.left) + postorder_rec(node.right) + [node.key]


def rev_preorder_rec(node):
    if node is None:
        return []
    return [node.key] + rev_preorder_rec(node.right) + rev_preorder_rec(node.left)


def rev_inorder_rec(node):
    if node is None:
        return []
    return rev_inorder_rec(node.right) + [node.key] + rev_inorder_rec(node.left)


def rev_postorder_rec(node):
    if node is None:
        return []
    return rev_postorder_rec(node.right) + rev_postorder_rec(node.left) + [node.key]


# ============================================================
# Helpers
# ============================================================


def mirror(node):
    """Structural mirror: left <-> right, keys preserved."""
    if node is None:
        return None
    m = Node(node.key)
    m.left = mirror(node.right)
    m.right = mirror(node.left)
    return m


def make_perfect_1_to_7() -> Node:
    """        4
             /   \
            2     6
           / \   / \
          1   3 5   7
    """
    return Node(
        4,
        Node(2, Node(1), Node(3)),
        Node(6, Node(5), Node(7)),
    )


def make_bst_from_keys(keys) -> BST:
    t = BST()
    for k in keys:
        t.insert(k)
    return t


# ============================================================
# Manual cases — empty / single
# ============================================================

ALL_TRAVERSALS = [
    preorder,
    inorder,
    postorder,
    reverse_preorder,
    reverse_inorder,
    reverse_postorder,
]


@pytest.mark.parametrize("f", ALL_TRAVERSALS)
def test_empty(f):
    assert f(None) == []


@pytest.mark.parametrize("f", ALL_TRAVERSALS)
def test_single(f):
    assert f(Node(42)) == [42]


# ============================================================
# Manual cases — perfect tree of 7 nodes
# ============================================================


def test_perfect_preorder():
    assert preorder(make_perfect_1_to_7()) == [4, 2, 1, 3, 6, 5, 7]


def test_perfect_inorder():
    assert inorder(make_perfect_1_to_7()) == [1, 2, 3, 4, 5, 6, 7]


def test_perfect_postorder():
    assert postorder(make_perfect_1_to_7()) == [1, 3, 2, 5, 7, 6, 4]


def test_perfect_reverse_preorder():
    assert reverse_preorder(make_perfect_1_to_7()) == [4, 6, 7, 5, 2, 3, 1]


def test_perfect_reverse_inorder():
    assert reverse_inorder(make_perfect_1_to_7()) == [7, 6, 5, 4, 3, 2, 1]


def test_perfect_reverse_postorder():
    assert reverse_postorder(make_perfect_1_to_7()) == [7, 5, 6, 3, 1, 2, 4]


# ============================================================
# Manual cases — degenerate shapes
# ============================================================


def test_left_chain_traversals():
    """Insert 5,4,3,2,1 -> left chain."""
    root = make_bst_from_keys([5, 4, 3, 2, 1]).root
    assert preorder(root) == [5, 4, 3, 2, 1]
    assert inorder(root) == [1, 2, 3, 4, 5]
    assert postorder(root) == [1, 2, 3, 4, 5]
    assert reverse_preorder(root) == [5, 4, 3, 2, 1]
    assert reverse_inorder(root) == [5, 4, 3, 2, 1]
    assert reverse_postorder(root) == [1, 2, 3, 4, 5]


def test_right_chain_traversals():
    root = make_bst_from_keys([1, 2, 3, 4, 5]).root
    assert preorder(root) == [1, 2, 3, 4, 5]
    assert inorder(root) == [1, 2, 3, 4, 5]
    assert postorder(root) == [5, 4, 3, 2, 1]
    assert reverse_preorder(root) == [1, 2, 3, 4, 5]
    assert reverse_inorder(root) == [5, 4, 3, 2, 1]
    assert reverse_postorder(root) == [5, 4, 3, 2, 1]


# ============================================================
# Unknown order string
# ============================================================


@pytest.mark.parametrize("bad", ["", "NNN", "XXX", "NLRX", "nLr"])
def test_traverse_unknown_order_raises(bad):
    with pytest.raises(ValueError):
        traverse(Node(1), bad)


# ============================================================
# traverse() dispatch matches wrappers
# ============================================================


def test_traverse_dispatch():
    root = make_perfect_1_to_7()
    assert traverse(root, "NLR") == preorder(root)
    assert traverse(root, "LNR") == inorder(root)
    assert traverse(root, "LRN") == postorder(root)
    assert traverse(root, "NRL") == reverse_preorder(root)
    assert traverse(root, "RNL") == reverse_inorder(root)
    assert traverse(root, "RLN") == reverse_postorder(root)


# ============================================================
# insert()
# ============================================================


def test_insert_into_empty():
    t = BST()
    assert t.root is None
    t.insert(5)
    assert t.root is not None
    assert t.root.key == 5
    assert t.root.left is None
    assert t.root.right is None


def test_insert_duplicate_is_noop():
    t = BST()
    t.insert(5)
    t.insert(5)
    t.insert(5)
    assert t.root.key == 5
    assert t.root.left is None
    assert t.root.right is None
    assert inorder(t.root) == [5]


def test_insert_preserves_bst_property():
    t = make_bst_from_keys([5, 3, 7, 1, 4, 6, 8, 2, 9, 0])
    assert validate_bst(t.root) is True


def test_insert_inorder_is_sorted():
    keys = [5, 3, 7, 1, 4, 6, 8, 2, 9, 0]
    t = make_bst_from_keys(keys)
    assert inorder(t.root) == sorted(keys)


def test_insert_left_placement():
    t = BST()
    for k in [10, 5, 3, 7]:
        t.insert(k)
    assert t.root.left.key == 5
    assert t.root.left.left.key == 3
    assert t.root.left.right.key == 7


def test_insert_right_placement():
    t = BST()
    for k in [10, 15, 12, 17]:
        t.insert(k)
    assert t.root.right.key == 15
    assert t.root.right.left.key == 12
    assert t.root.right.right.key == 17


# ============================================================
# Random BSTs: insert validity + traversals vs oracles
# ============================================================


@pytest.mark.parametrize("n", [0, 1, 2, 3, 5, 10, 20, 50, 100])
@pytest.mark.parametrize("seed", range(10))
def test_random_bst_all(n, seed):
    rng = random.Random(seed)
    keys = rng.sample(range(-1000, 1000), n)
    t = make_bst_from_keys(keys)

    # insert() must maintain the BST property
    assert validate_bst(t.root) is True

    # Every traversal must match its independent recursive oracle
    assert preorder(t.root) == preorder_rec(t.root)
    assert inorder(t.root) == inorder_rec(t.root)
    assert postorder(t.root) == postorder_rec(t.root)
    assert reverse_preorder(t.root) == rev_preorder_rec(t.root)
    assert reverse_inorder(t.root) == rev_inorder_rec(t.root)
    assert reverse_postorder(t.root) == rev_postorder_rec(t.root)

    # Structural properties of BST
    assert inorder(t.root) == sorted(keys)
    assert reverse_inorder(t.root) == sorted(keys, reverse=True)


# ============================================================
# Cross-check: reverse traversals as mirror-tree traversals
# ============================================================


@pytest.mark.parametrize("seed", range(10))
def test_reverse_preorder_is_preorder_of_mirror(seed):
    rng = random.Random(seed)
    keys = rng.sample(range(-1000, 1000), 20)
    t = make_bst_from_keys(keys)
    m = mirror(t.root)
    assert reverse_preorder(t.root) == preorder_rec(m)


@pytest.mark.parametrize("seed", range(10))
def test_reverse_postorder_is_postorder_of_mirror(seed):
    rng = random.Random(seed)
    keys = rng.sample(range(-1000, 1000), 20)
    t = make_bst_from_keys(keys)
    m = mirror(t.root)
    assert reverse_postorder(t.root) == postorder_rec(m)


@pytest.mark.parametrize("seed", range(10))
def test_reverse_inorder_is_reversed_inorder(seed):
    rng = random.Random(seed)
    keys = rng.sample(range(-1000, 1000), 20)
    t = make_bst_from_keys(keys)
    assert reverse_inorder(t.root) == list(reversed(inorder(t.root)))


# ============================================================
# Deep chains: iterative traversals must not hit RecursionError
# ============================================================


@pytest.mark.parametrize("n", [1, 10, 100, 500])
def test_left_chain_deep(n):
    t = make_bst_from_keys(list(range(n, 0, -1)))  # n, n-1, ..., 1
    assert validate_bst(t.root) is True
    for f in ALL_TRAVERSALS:
        result = f(t.root)
        assert len(result) == n
        assert sorted(result) == list(range(1, n + 1))


@pytest.mark.parametrize("n", [1, 10, 100, 500])
def test_right_chain_deep(n):
    t = make_bst_from_keys(list(range(1, n + 1)))  # 1, 2, ..., n
    assert validate_bst(t.root) is True
    for f in ALL_TRAVERSALS:
        result = f(t.root)
        assert len(result) == n
        assert sorted(result) == list(range(1, n + 1))


# ============================================================
# Combined: random insert, chain of re-verifications
# ============================================================


@pytest.mark.parametrize("seed", range(20))
def test_insert_stepwise_keeps_bst(seed):
    """After each insert, the tree is still a valid BST and in-order is sorted."""
    rng = random.Random(seed)
    keys = rng.sample(range(-500, 500), 30)
    t = BST()
    seen: list[int] = []
    for k in keys:
        t.insert(k)
        seen.append(k)
        assert validate_bst(t.root) is True
        assert inorder(t.root) == sorted(seen)


if __name__ == "__main__":
    pytest.main()
