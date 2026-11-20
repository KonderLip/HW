"""Тесты задачи 3.

Что проверяем:
- API put/get работает.
- get отсутствующего ключа возвращает default.
- Eviction по LRU (capacity=2, put A/B/C -> A вылетает).
- Recency: get(A) переводит A в MRU (B вылетает вместо A).
- len(cache) и `key in cache`.
- Умеренный concurrent stress (4 thread'а * 10k ops) - никаких exception,
  size <= capacity, cache не пуст в конце.

Запуск из папки задачи: pytest -v
"""

import threading

import pytest

from thread_safe_lru import LRUCache


# ---------------------------------------------------------------------
# Basic API
# ---------------------------------------------------------------------


def test_put_get_basic() -> None:
    cache: LRUCache[str, int] = LRUCache(capacity=10)
    cache.put("a", 1)
    assert cache.get("a") == 1


def test_get_missing_no_default_returns_none() -> None:
    cache: LRUCache[str, int] = LRUCache(capacity=10)
    assert cache.get("missing") is None


def test_get_missing_with_default() -> None:
    cache: LRUCache[str, int] = LRUCache(capacity=10)
    assert cache.get("missing", default=-1) == -1


def test_capacity_zero_rejected() -> None:
    with pytest.raises(ValueError, match=">= 1"):
        LRUCache[str, int](capacity=0)


def test_capacity_negative_rejected() -> None:
    with pytest.raises(ValueError, match=">= 1"):
        LRUCache[str, int](capacity=-3)


def test_len_empty() -> None:
    cache: LRUCache[str, int] = LRUCache(capacity=10)
    assert len(cache) == 0


def test_len_after_puts() -> None:
    cache: LRUCache[str, int] = LRUCache(capacity=10)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)
    assert len(cache) == 3


def test_len_capped_by_capacity() -> None:
    cache: LRUCache[str, int] = LRUCache(capacity=3)
    for i in range(10):
        cache.put(f"k{i}", i)
    assert len(cache) == 3


def test_contains_true() -> None:
    cache: LRUCache[str, int] = LRUCache(capacity=10)
    cache.put("a", 1)
    assert "a" in cache


def test_contains_false() -> None:
    cache: LRUCache[str, int] = LRUCache(capacity=10)
    cache.put("a", 1)
    assert "b" not in cache


# ---------------------------------------------------------------------
# LRU semantics
# ---------------------------------------------------------------------


def test_eviction_evicts_oldest() -> None:
    """capacity=2, put A/B/C -> A evicted, B и C остались."""
    cache: LRUCache[str, int] = LRUCache(capacity=2)
    cache.put("A", 1)
    cache.put("B", 2)
    cache.put("C", 3)
    assert "A" not in cache
    assert "B" in cache
    assert "C" in cache


def test_recency_updated_by_get() -> None:
    """capacity=2, put A/B, get A, put C -> B evicted (не A)."""
    cache: LRUCache[str, int] = LRUCache(capacity=2)
    cache.put("A", 1)
    cache.put("B", 2)
    assert cache.get("A") == 1  # touch A -> A становится MRU
    cache.put("C", 3)
    assert "A" in cache, "A должен был остаться - его только что get'нули"
    assert "B" not in cache
    assert "C" in cache


def test_recency_updated_by_put_of_existing() -> None:
    """put существующего ключа тоже переводит его в MRU + обновляет значение."""
    cache: LRUCache[str, int] = LRUCache(capacity=2)
    cache.put("A", 1)
    cache.put("B", 2)
    cache.put("A", 100)  # update A -> A становится MRU
    cache.put("C", 3)
    assert cache.get("A") == 100
    assert "B" not in cache
    assert "C" in cache


def test_get_missing_does_not_touch_recency() -> None:
    """Промах get'а не должен что-либо вытеснять / менять порядок."""
    cache: LRUCache[str, int] = LRUCache(capacity=2)
    cache.put("A", 1)
    cache.put("B", 2)
    assert cache.get("nope") is None
    # порядок не сдвинулся: A всё ещё LRU
    cache.put("C", 3)
    assert "A" not in cache
    assert "B" in cache
    assert "C" in cache


def test_capacity_one() -> None:
    """Пограничный кейс: capacity=1 - только последний put выживает."""
    cache: LRUCache[str, int] = LRUCache(capacity=1)
    cache.put("A", 1)
    cache.put("B", 2)
    assert "A" not in cache
    assert cache.get("B") == 2
    assert len(cache) == 1


# ---------------------------------------------------------------------
# Concurrency (public smoke stress)
# ---------------------------------------------------------------------


def test_concurrent_stress_public() -> None:
    """4 thread'а * 10k mixed ops. Не должно быть exception, size <= cap."""
    cap = 100
    cache: LRUCache[int, int] = LRUCache(capacity=cap)
    ops_per_thread = 10_000
    n_threads = 4

    errors: list[BaseException] = []
    errors_lock = threading.Lock()
    barrier = threading.Barrier(n_threads)

    def worker(tid: int) -> None:
        try:
            barrier.wait()
            for i in range(ops_per_thread):
                # общий keyspace на 500 ключей > cap -> реальный churn с eviction.
                k = (tid * ops_per_thread + i) % 500
                if i % 2 == 0:
                    cache.put(k, tid * 1_000_000 + i)
                else:
                    cache.get(k, default=-1)
        except BaseException as exc:  # ловим что угодно
            with errors_lock:
                errors.append(exc)

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30.0)
        assert not t.is_alive(), "worker завис - deadlock?"

    assert not errors, f"exception в workers: {errors[:3]}"
    assert len(cache) <= cap, f"size {len(cache)} > capacity {cap}"
    # После 40k put'ов в keyspace=500 c cap=100 - cache должен быть заполнен.
    assert len(cache) > 0, "cache пустой после stress - что-то удаляет лишнее"
