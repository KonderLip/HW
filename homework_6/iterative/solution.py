from typing import List, Optional

import random

from homework_6.compare.solution import _merge, _partition


def mergesort(arr: List[int]) -> List[int]:
    n = len(arr)
    result = arr.copy()
    if n <= 1:
        return result

    buf = [0] * n
    width = 1
    while width < n:
        lo = 0
        while lo < n:
            mid = min(lo + width, n)
            hi = min(lo + 2 * width, n)
            # skip the merge if halves are already ordered
            if mid < hi and result[mid - 1] > result[mid]:
                _merge(result, buf, lo, mid, hi)
            lo += 2 * width
        width *= 2

    return result


def quicksort(arr: List[int], rng: Optional[random.Random] = None) -> List[int]:
    rng = rng if rng is not None else random
    result = arr.copy()
    n = len(result)
    if n <= 1:
        return result

    stack = [(0, n)]
    while stack:
        lo, hi = stack.pop()
        if hi - lo <= 1:
            continue
        p = _partition(result, lo, hi, rng)
        left_size = p + 1 - lo
        right_size = hi - (p + 1)
        if left_size < right_size:
            if p + 1 < hi:
                stack.append((p + 1, hi))
            if lo < p + 1:
                stack.append((lo, p + 1))
        else:
            if lo < p + 1:
                stack.append((lo, p + 1))
            if p + 1 < hi:
                stack.append((p + 1, hi))

    return result
