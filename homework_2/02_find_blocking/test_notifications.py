"""Тесты задачи 2. Запуск из папки задачи: pytest -v"""

import asyncio
import time

from notifications import notify_all, send_email

USERS = ["anna", "boris", "vera", "gleb"]


def test_send_email_result() -> None:
    assert asyncio.run(send_email("anna")) == "anna: 33 символов"


def test_notify_all_result() -> None:
    results = asyncio.run(notify_all(USERS))
    assert results == [f"{u}: {len(f'Привет, {u}! У нас новые скидки.')} символов" for u in USERS]


def test_notify_all_is_concurrent() -> None:
    start = time.perf_counter()
    asyncio.run(notify_all(USERS))
    elapsed = time.perf_counter() - start
    assert elapsed < 1.0, (
        f"4 письма ушли за {elapsed:.2f}s - значит по одному. "
        "Где-то event loop блокируется."
    )


def test_event_loop_not_blocked() -> None:
    """Пока идёт рассылка, другие корутины должны продолжать работать."""
    ticks = 0

    async def ticker() -> None:
        nonlocal ticks
        for _ in range(4):
            await asyncio.sleep(0.1)
            ticks += 1

    async def main() -> None:
        await asyncio.gather(notify_all(["anna"]), ticker())

    start = time.perf_counter()
    asyncio.run(main())
    elapsed = time.perf_counter() - start
    assert ticks == 4
    assert elapsed < 0.7, f"{elapsed:.2f}s: ticker стоял, пока отправлялось письмо"
