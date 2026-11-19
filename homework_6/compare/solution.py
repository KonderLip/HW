from typing import List, Tuple, Optional

import functools
import random
import time


def mergesort(arr: List[int]) -> List[int]:
    result = arr.copy()
    buffer = [0] * len(arr)
    _msort(result, buffer, 0, len(arr))
    return result


def _msort(arr: List[int], buf: List[int], lo: int, hi: int) -> None:
    if hi - lo <= 1:
        return
    mid = (lo + hi) // 2
    _msort(arr, buf, lo, mid)
    _msort(arr, buf, mid, hi)
    if arr[mid - 1] <= arr[mid]:
        return
    _merge(arr, buf, lo, mid, hi)


def _merge(arr: List[int], buf: List[int], lo: int, mid: int, hi: int) -> None:
    i, j, k = lo, mid, lo
    while i < mid and j < hi:
        if arr[i] <= arr[j]:
            buf[k] = arr[i]
            i += 1
        else:
            buf[k] = arr[j]
            j += 1
        k += 1
    while i < mid:
        buf[k] = arr[i]
        i += 1
        k += 1
    while j < hi:
        buf[k] = arr[j]
        j += 1
        k += 1
    arr[lo:hi] = buf[lo:hi]


def quicksort(arr: List[int], rng: Optional[random.Random] = None) -> List[int]:
    rng = rng if rng is not None else random
    result = arr.copy()
    _qsort(result, 0, len(result), rng)
    return result


def _qsort(arr: List[int], lo: int, hi: int, rng: random.Random) -> None:
    if hi - lo <= 1:
        return
    p = _partition(arr, lo, hi, rng)
    _qsort(arr, lo, p + 1, rng)
    _qsort(arr, p + 1, hi, rng)


def _partition(a: List[int], lo: int, hi: int, rng: random.Random) -> int:
    pivot = a[rng.randint(lo, hi - 1)]
    i = lo - 1
    j = hi
    while True:
        i += 1
        while a[i] < pivot:
            i += 1
        j -= 1
        while a[j] > pivot:
            j -= 1
        if i >= j:
            return j
        a[i], a[j] = a[j], a[i]


def timed(func):
    records: List[Tuple[str, float]] = []

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - start
            records.append((func.__name__, elapsed))

    wrapper.records = records
    wrapper.last = lambda: records[-1][1] if records else None
    wrapper.clear = records.clear
    return wrapper
