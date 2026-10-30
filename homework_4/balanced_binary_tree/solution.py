from homework_4.tree import Node


def main(root: Node | None) -> bool:
    if not root:
        return True
    stack = [(root, False)]
    h = []
    while stack:
        node, visited = stack.pop()
        if not node:
            h.append(0)
        elif not visited:
            stack.append((node, True))
            stack.append((node.right, False))
            stack.append((node.left, False))
        else:
            right_h = h.pop()
            left_h = h.pop()
            if abs(left_h - right_h) > 1:
                return False
            h.append(max(left_h, right_h) + 1)
    return True
