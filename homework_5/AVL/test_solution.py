import random
import sys

import pytest

from solution import AVL, Node, _balance_factor, _height

sys.setrecursionlimit(10_000)


# ============================================================
# Invariant checkers
# ============================================================


def check_bst(node: Node | None, lo=float("-inf"), hi=float("+inf")) -> None:
    """Every key must be strictly within (lo, hi). Fails with assert."""
    if node is None:
        return
    assert lo < node.key < hi, f"BST order violated at {node.key}"
    check_bst(node.left, lo, node.key)
    check_bst(node.right, node.key, hi)


def check_balance(node: Node | None) -> None:
    """AVL invariant: |bf| <= 1 and heights are correct at every node."""
    if node is None:
        return
    check_balance(node.left)
    check_balance(node.right)
    bf = _balance_factor(node)
    assert abs(bf) <= 1, f"balance violated at {node.key}: bf={bf}"
    expected_h = 1 + max(_height(node.left), _height(node.right))
    assert node.height == expected_h, f"height wrong at {node.key}"


def check_all(avl: AVL) -> None:
    check_bst(avl.root)
    check_balance(avl.root)


def inorder(node: Node | None) -> list[int]:
    if node is None:
        return []
    return inorder(node.left) + [node.key] + inorder(node.right)


def collect_keys(avl: AVL) -> list[int]:
    return inorder(avl.root)


# ============================================================
# Empty tree
# ============================================================


def test_empty_search():
    avl = AVL()
    assert avl.search(10) is False


def test_empty_delete():
    avl = AVL()
    assert avl.delete(10) is False


def test_empty_root_is_none():
    avl = AVL()
    assert avl.root is None


# ============================================================
# Single node
# ============================================================


def test_single_insert_search():
    avl = AVL()
    avl.insert(42)
    assert avl.root is not None
    assert avl.root.key == 42
    assert avl.root.height == 1
    assert avl.root.left is None
    assert avl.root.right is None
    assert avl.search(42) is True
    assert avl.search(41) is False
    assert avl.search(43) is False


def test_single_delete():
    avl = AVL()
    avl.insert(42)
    assert avl.delete(42) is True
    assert avl.root is None
    assert avl.search(42) is False
    assert avl.delete(42) is False


# ============================================================
# Basic insert/search
# ============================================================


def test_insert_multiple():
    avl = AVL()
    for k in [10, 5, 15, 3, 7, 12, 17]:
        avl.insert(k)
    assert collect_keys(avl) == [3, 5, 7, 10, 12, 15, 17]
    check_all(avl)


def test_insert_duplicate_is_noop():
    avl = AVL()
    avl.insert(5)
    avl.insert(5)
    avl.insert(5)
    assert collect_keys(avl) == [5]
    assert avl.root is not None
    assert avl.root.left is None
    assert avl.root.right is None


def test_search_after_many_inserts():
    avl = AVL()
    keys = [50, 30, 70, 20, 40, 60, 80]
    for k in keys:
        avl.insert(k)
    for k in keys:
        assert avl.search(k) is True
    for k in [10, 35, 65, 90, -5]:
        assert avl.search(k) is False


# ============================================================
# Rotations — explicit, one test per case
# ============================================================


def test_rotation_ll():
    """Insert 30, 20, 10 -> single right rotation."""
    avl = AVL()
    for k in [30, 20, 10]:
        avl.insert(k)
    check_all(avl)
    assert avl.root is not None
    assert avl.root.key == 20
    assert avl.root.left is not None and avl.root.left.key == 10
    assert avl.root.right is not None and avl.root.right.key == 30


def test_rotation_rr():
    """Insert 10, 20, 30 -> single left rotation."""
    avl = AVL()
    for k in [10, 20, 30]:
        avl.insert(k)
    check_all(avl)
    assert avl.root is not None
    assert avl.root.key == 20
    assert avl.root.left is not None and avl.root.left.key == 10
    assert avl.root.right is not None and avl.root.right.key == 30


def test_rotation_lr():
    """Insert 30, 10, 20 -> double rotation (left on left, then right on root)."""
    avl = AVL()
    for k in [30, 10, 20]:
        avl.insert(k)
    check_all(avl)
    assert avl.root is not None
    assert avl.root.key == 20
    assert avl.root.left is not None and avl.root.left.key == 10
    assert avl.root.right is not None and avl.root.right.key == 30


def test_rotation_rl():
    """Insert 10, 30, 20 -> double rotation."""
    avl = AVL()
    for k in [10, 30, 20]:
        avl.insert(k)
    check_all(avl)
    assert avl.root is not None
    assert avl.root.key == 20
    assert avl.root.left is not None and avl.root.left.key == 10
    assert avl.root.right is not None and avl.root.right.key == 30


def test_rotations_keeps_balance_through_sequence():
    """Sorted insert — AVL must rebalance on the fly."""
    avl = AVL()
    for k in range(1, 16):
        avl.insert(k)
        check_all(avl)
    assert collect_keys(avl) == list(range(1, 16))


# ============================================================
# Delete — three cases: leaf, one child, two children
# ============================================================


def _make_tree(keys):
    avl = AVL()
    for k in keys:
        avl.insert(k)
    return avl


def test_delete_leaf():
    avl = _make_tree([10, 5, 15])
    assert avl.delete(5) is True
    assert collect_keys(avl) == [10, 15]
    check_all(avl)


def test_delete_node_with_one_child_left():
    avl = _make_tree([10, 5, 15, 3])
    assert avl.delete(5) is True
    assert collect_keys(avl) == [3, 10, 15]
    check_all(avl)


def test_delete_node_with_one_child_right():
    avl = _make_tree([10, 5, 15, 7])
    assert avl.delete(5) is True
    assert collect_keys(avl) == [7, 10, 15]
    check_all(avl)


def test_delete_node_with_two_children():
    avl = _make_tree([20, 10, 30, 25, 40, 22, 27])
    assert avl.delete(25) is True  # node with two children
    check_all(avl)
    assert 25 not in collect_keys(avl)


def test_delete_root():
    avl = _make_tree([10, 5, 15, 3, 7, 12, 17])
    assert avl.delete(10) is True
    check_all(avl)
    assert 10 not in collect_keys(avl)
    assert collect_keys(avl) == [3, 5, 7, 12, 15, 17]


def test_delete_only_root():
    avl = _make_tree([10])
    assert avl.delete(10) is True
    assert avl.root is None


def test_delete_missing():
    avl = _make_tree([10, 5, 15])
    assert avl.delete(99) is False
    check_all(avl)
    assert collect_keys(avl) == [5, 10, 15]


def test_delete_all_then_empty():
    keys = [50, 25, 75, 10, 35, 60, 90, 5, 15, 30, 40, 55, 65, 85, 95]
    avl = _make_tree(keys)
    for k in keys:
        assert avl.delete(k) is True
        check_all(avl)
    assert avl.root is None


def test_delete_preserves_balance_through_sequence():
    avl = _make_tree(range(1, 32))
    for k in range(1, 32):
        assert avl.delete(k) is True
        check_all(avl)
    assert avl.root is None


def test_delete_leaf_rebalances():
    """Two-child delete deep in the tree must trigger rebalance on the way up."""
    avl = _make_tree([50, 30, 70, 20, 40, 60, 80, 10, 25, 35, 45])
    check_all(avl)
    assert avl.delete(80) is True
    check_all(avl)
    assert avl.delete(70) is True
    check_all(avl)


# ============================================================
# Interleaved insert / delete / search
# ============================================================


def test_interleaved_operations():
    avl = AVL()
    ops = [
        ("i", 10),
        ("i", 20),
        ("i", 5),
        ("s", 10),
        ("s", 15),
        ("d", 20),
        ("i", 15),
        ("i", 25),
        ("s", 20),
        ("s", 15),
        ("d", 5),
        ("d", 10),
        ("s", 10),
        ("s", 25),
        ("i", 30),
    ]
    for op, k in ops:
        if op == "i":
            avl.insert(k)
        elif op == "d":
            avl.delete(k)
        else:
            # just call; final checks below
            avl.search(k)
        check_all(avl)

    assert collect_keys(avl) == [15, 25, 30]
    assert avl.search(10) is False
    assert avl.search(15) is True
    assert avl.search(25) is True
    assert avl.search(30) is True


# ============================================================
# Oracle: naive set-based reference
# ============================================================


class SetOracle:
    def __init__(self):
        self.data: set[int] = set()

    def insert(self, key):
        self.data.add(key)

    def delete(self, key):
        had = key in self.data
        self.data.discard(key)
        return had

    def search(self, key):
        return key in self.data


@pytest.mark.parametrize("seed", range(20))
def test_random_ops_vs_oracle(seed):
    rng = random.Random(seed)
    avl = AVL()
    oracle = SetOracle()

    for _ in range(200):
        op = rng.choice(["insert", "delete", "search"])
        key = rng.randint(-100, 100)

        if op == "insert":
            avl.insert(key)
            oracle.insert(key)
        elif op == "delete":
            assert avl.delete(key) == oracle.delete(key)
        else:
            assert avl.search(key) == oracle.search(key)

        check_all(avl)

    assert collect_keys(avl) == sorted(oracle.data)


# ============================================================
# Repeated keys: insert/delete churn
# ============================================================


@pytest.mark.parametrize("seed", range(10))
def test_duplicate_churn(seed):
    """Insert all keys, then churn duplicates — the tree never grows."""
    rng = random.Random(seed)
    avl = AVL()
    keys = [5, 10, 15, 20, 25]

    # Pre-populate, so the invariant below holds from the very first check.
    for k in keys:
        avl.insert(k)
    check_all(avl)
    assert collect_keys(avl) == sorted(keys)

    for _ in range(50):
        k = rng.choice(keys)
        avl.insert(k)  # duplicate — must be a no-op
        check_all(avl)
        assert collect_keys(avl) == sorted(keys)


# ============================================================
# Deep trees: stack overflow safety
# ============================================================


def test_deep_insert_sorted():
    """2000 inserts of sorted values -> AVL stays shallow, recursion fine."""
    avl = AVL()
    n = 2000
    for k in range(n):
        avl.insert(k)
        if k % 100 == 0:
            check_all(avl)
    check_all(avl)
    assert _height(avl.root) <= 2 * (n.bit_length() + 1)  # loose bound


def test_deep_insert_reverse_sorted():
    avl = AVL()
    n = 2000
    for k in range(n, 0, -1):
        avl.insert(k)
    check_all(avl)
    assert collect_keys(avl) == list(range(1, n + 1))


def test_deep_delete_all():
    avl = AVL()
    n = 500
    for k in range(n):
        avl.insert(k)
    for k in range(n):
        assert avl.delete(k) is True
        if k % 50 == 0:
            check_all(avl)
    assert avl.root is None


# ============================================================
# Height bound: AVL guarantees h <= 1.44 * log2(n + 2)
# ============================================================


@pytest.mark.parametrize("n", [1, 10, 100, 500, 1000])
def test_avl_height_bound(n):
    import math

    avl = AVL()
    rng = random.Random(n)
    keys = rng.sample(range(-(10**6), 10**6), n)
    for k in keys:
        avl.insert(k)

    h = _height(avl.root)
    bound = 1.44 * math.log2(n + 2)
    assert h <= bound + 1, f"height {h} exceeds AVL bound {bound:.2f} for n={n}"


if __name__ == "__main__":
    pytest.main()
