from dataclasses import dataclass


@dataclass(repr=False, eq=False, slots=True)
class Node:
    key: int
    left: "Node | None" = None
    right: "Node | None" = None
