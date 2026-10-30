from homework_4.tree import Node


def main(root: Node | None) -> bool:
    if not root:
        return True
    stack = [(root, float("-inf"), float("+inf"))]
    while stack:
        node, lower, upper = stack.pop()
        if not (lower < node.key < upper):
            return False
        if node.right:
            stack.append((node.right, node.key, upper))
        if node.left:
            stack.append((node.left, lower, node.key))
    return True
