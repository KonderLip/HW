"""Тесты задачи 1. Запуск из папки задачи: pytest -v"""

import asyncio
import time

import pytest

import prices
from prices import (
    get_price_or_none,
    get_prices_concurrent,
    get_prices_limited,
    get_prices_sequential,
    get_prices_with_timeout,
)

SHOPS = ["ozon", "wb", "yandex"]  # задержки 0.3 + 0.2 + 0.4 = 0.9 с, максимум 0.4 с


def run_timed(coro):  # type: ignore[no-untyped-def]
    start = time.perf_counter()
    result = asyncio.run(coro)
    return result, time.perf_counter() - start


# ---------- 1.1 ----------


def test_sequential_result() -> None:
    result, _ = run_timed(get_prices_sequential(SHOPS))
    assert result == [990, 950, 1100]


def test_sequential_empty() -> None:
    result, _ = run_timed(get_prices_sequential([]))
    assert result == []


def test_sequential_takes_sum_of_delays() -> None:
    _, elapsed = run_timed(get_prices_sequential(SHOPS))
    assert elapsed >= 0.85, f"{elapsed:.2f}s: запросы должны идти по очереди (~0.9 с)"


# ---------- 1.2 ----------


def test_concurrent_result_keeps_order() -> None:
    result, _ = run_timed(get_prices_concurrent(SHOPS))
    assert result == [990, 950, 1100]


def test_concurrent_empty() -> None:
    result, _ = run_timed(get_prices_concurrent([]))
    assert result == []


def test_concurrent_takes_max_delay() -> None:
    _, elapsed = run_timed(get_prices_concurrent(SHOPS))
    assert elapsed < 0.6, f"{elapsed:.2f}s: запросы должны идти одновременно (~0.4 с)"


# ---------- 1.3 ----------


def test_price_or_none_fast_shop() -> None:
    result, _ = run_timed(get_price_or_none("wb", timeout=1.0))
    assert result == 950


def test_price_or_none_slow_shop() -> None:
    result, elapsed = run_timed(get_price_or_none("slow_shop", timeout=0.5))
    assert result is None
    assert elapsed < 1.0, f"{elapsed:.2f}s: нельзя ждать медленный магазин дольше таймаута"


def test_with_timeout_mixed() -> None:
    result, elapsed = run_timed(get_prices_with_timeout(SHOPS + ["slow_shop"], timeout=1.0))
    assert result == [990, 950, 1100, None]
    assert elapsed < 1.5, f"{elapsed:.2f}s: запросы должны идти одновременно"


# ---------- 1.4 (дополнительная) ----------


def test_limited(monkeypatch: pytest.MonkeyPatch) -> None:
    """20 магазинов по 0.1 с, limit=3 -> не больше 3 запросов одновременно."""
    in_flight = 0
    peak = 0

    async def tracking_fetch_price(shop: str) -> int:
        nonlocal in_flight, peak
        in_flight += 1
        peak = max(peak, in_flight)
        await asyncio.sleep(0.1)
        in_flight -= 1
        return len(shop)

    monkeypatch.setattr(prices, "fetch_price", tracking_fetch_price)
    shops = [f"shop_{i}" for i in range(20)]

    result, elapsed = run_timed(get_prices_limited(shops, limit=3))

    assert result == [len(s) for s in shops]
    assert peak == 3, f"одновременно шло {peak} запросов, а нужно не больше 3 (и не по одному)"
    assert elapsed < 1.5, f"{elapsed:.2f}s: 20 запросов по 3 за раз должны занять ~0.7 с"
