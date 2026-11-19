from typing import List, Tuple, Optional

import random


def main(nums: List[int], k: int, rng: Optional[random.Random] = None) -> int:
    n = len(nums)
    if not 1 <= k <= n:
        raise ValueError(f"k={k} out of range [1, {n}]")
    rng = rng if rng is not None else random
    target = n - k
    arr = nums.copy()
    lo, hi = 0, n
    while hi - lo > 1:
        pivot = arr[rng.randint(lo, hi - 1)]
        lt, gt = _partition_3way(arr, lo, hi, pivot)
        if target < lt:
            hi = lt
        elif target >= gt:
            lo = gt
        else:
            return pivot
    return arr[lo]


def _partition_3way(arr: List[int], lo: int, hi: int, pivot: int) -> Tuple[int, int]:
    lt = i = lo
    gt = hi
    while i < gt:
        if arr[i] < pivot:
            arr[lt], arr[i] = arr[i], arr[lt]
            lt += 1
            i += 1
        elif arr[i] > pivot:
            gt -= 1
            arr[i], arr[gt] = arr[gt], arr[i]
        else:
            i += 1
    return lt, gt


if __name__ == "__main__":
    print(main([3, 2, 1, 5, 6, 4], 2))
    print(main([3, 2, 3, 1, 2, 4, 5, 5, 6], 4))
