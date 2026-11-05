from dataclasses import dataclass
from typing import Tuple


@dataclass(repr=False, eq=False, slots=True)
class Node:
    key: int
    left: "Node | None" = None
    right: "Node | None" = None
    height: int = 1


def _height(node: Node | None) -> int:
    return node.height if node is not None else 0


def _update(node: Node) -> None:
    node.height = 1 + max(_height(node.left), _height(node.right))


def _rotate_left(x: Node) -> Node:
    y = x.right
    x.right = y.left
    y.left = x
    _update(x)
    _update(y)
    return y


def _rotate_right(y: Node) -> Node:
    x = y.left
    y.left = x.right
    x.right = y
    _update(y)
    _update(x)
    return x


def _balance_factor(node: Node) -> int:
    return _height(node.left) - _height(node.right) if node else 0


def _rebalance(node: Node) -> Node:
    _update(node)
    bf = _balance_factor(node)
    if bf > 1:
        if _balance_factor(node.left) < 0:  # LR
            node.left = _rotate_left(node.left)
        return _rotate_right(node)  # LL
    if bf < -1:
        if _balance_factor(node.right) > 0:  # RL
            node.right = _rotate_right(node.right)
        return _rotate_left(node)  # RR
    return node


class AVL:
    def __init__(self):
        self.root: Node | None = None

    def search(self, key: int) -> bool:
        cur = self.root
        while cur is not None:
            if key == cur.key:
                return True
            cur = cur.left if key < cur.key else cur.right
        return False

    def insert(self, key: int) -> None:
        self.root = self._insert(self.root, key)

    def _insert(self, node: Node | None, key: int) -> Node:
        if node is None:
            return Node(key)
        if key < node.key:
            node.left = self._insert(node.left, key)
        elif key > node.key:
            node.right = self._insert(node.right, key)
        else:
            return node
        return _rebalance(node)

    def delete(self, key: int) -> bool:
        found, self.root = self._delete(self.root, key)
        return found

    def _delete(self, node: Node | None, key: int) -> Tuple[bool, Node | None]:
        if node is None:
            return False, None
        if key < node.key:
            found, node.left = self._delete(node.left, key)
            if not found:
                return False, node
        elif key > node.key:
            found, node.right = self._delete(node.right, key)
            if not found:
                return False, node
        else:
            if node.left is None:
                return True, node.right
            if node.right is None:
                return True, node.left
            succ = node.right
            while succ.left is not None:
                succ = succ.left
            node.key = succ.key
            _, node.right = self._delete(node.right, succ.key)
        return True, _rebalance(node)
