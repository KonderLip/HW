from typing import List

from homework_4.tree import Node


class BST:
    def __init__(self):
        self.root: Node | None = None

    def insert(self, key: int) -> None:
        if not self.root:
            self.root = Node(key)
            return

        cur = self.root
        while True:
            if key < cur.key:
                if not cur.left:
                    cur.left = Node(key)
                    return
                cur = cur.left
            elif key > cur.key:
                if not cur.right:
                    cur.right = Node(key)
                    return
                cur = cur.right
            else:
                return


def traverse(root: Node | None, order: str) -> List[int]:
    if root is None:
        return []

    result = []
    stack = [(root, False)]

    while stack:
        node, visited = stack.pop()

        if visited:
            result.append(node.key)
            continue

        match order:
            case "NLR":  # preorder
                result.append(node.key)
                if node.right:
                    stack.append((node.right, False))
                if node.left:
                    stack.append((node.left, False))

            case "LNR":  # inorder
                if node.right:
                    stack.append((node.right, False))
                stack.append((node, True))
                if node.left:
                    stack.append((node.left, False))

            case "LRN":  # postorder
                stack.append((node, True))
                if node.right:
                    stack.append((node.right, False))
                if node.left:
                    stack.append((node.left, False))

            case "NRL":  # reverse preorder
                result.append(node.key)
                if node.left:
                    stack.append((node.left, False))
                if node.right:
                    stack.append((node.right, False))

            case "RNL":  # reverse inorder
                if node.left:
                    stack.append((node.left, False))
                stack.append((node, True))
                if node.right:
                    stack.append((node.right, False))

            case "RLN":  # reverse postorder
                stack.append((node, True))
                if node.left:
                    stack.append((node.left, False))
                if node.right:
                    stack.append((node.right, False))

            case _:
                raise ValueError(f"unknown order: {order}")

    return result


def preorder(root: Node | None) -> List[int]:
    return traverse(root, "NLR")


def inorder(root: Node | None) -> List[int]:
    return traverse(root, "LNR")


def postorder(root: Node | None) -> List[int]:
    return traverse(root, "LRN")


def reverse_preorder(root: Node | None) -> List[int]:
    return traverse(root, "NRL")


def reverse_inorder(root: Node | None) -> List[int]:
    return traverse(root, "RNL")


def reverse_postorder(root: Node | None) -> List[int]:
    return traverse(root, "RLN")
