from typing import List, Tuple


def main(arr: List[int], k: int) -> Tuple[int, int]:
    ids = {}
    for idx, val in enumerate(arr):
        prev_idx = ids.get(k - val)
        if prev_idx is not None:
            return prev_idx, idx
        ids[val] = idx
    raise ValueError


if __name__ == "__main__":
    print(*main([1, 3, 4, 10], 7))
    print(*main([5, 5, 1, 4], 10))
