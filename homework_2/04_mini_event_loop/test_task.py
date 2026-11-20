"""Тесты бонусной задачи. Запуск из папки задачи: pytest -v

Проверяют что твой AwaitTask/await_task:
- работает как await task в asyncio (блок до completion, возврат результата);
- не polling'ует (проверяется через wall-clock);
- корректно обрабатывает уже завершённые task'и (fast path);
- ловит deadlock;
- позволяет multiple waiter'ов на одну task'у.
"""

import time
from collections.abc import Generator
from typing import Any

import pytest

from mini_asyncio import AwaitTask, await_task, create_task, run, sleep

Task = Generator[Any, Any, Any]


def test_await_task_syscall_dataclass_exists() -> None:
    """AwaitTask должен быть простой dataclass с полем tid."""
    s = AwaitTask(tid=42)
    assert s.tid == 42


def test_single_await_returns_result() -> None:
    """result = yield from await_task(tid) возвращает return value coro."""
    result_holder: list[Any] = []

    def child() -> Task:
        yield from sleep(0.05)
        return "hello"

    def main() -> Task:
        tid = create_task(child())
        result = yield from await_task(tid)
        result_holder.append(result)

    run(main())
    assert result_holder == ["hello"]


def test_await_parallel_tasks_wall_clock() -> None:
    """Два fetch'а по 0.1s + await'ы - total wall-clock ~0.1, не 0.2."""

    def fetch(delay: float, val: str) -> Task:
        yield from sleep(delay)
        return val

    results: list[str] = []

    def main() -> Task:
        tid_a = create_task(fetch(0.1, "A"))
        tid_b = create_task(fetch(0.1, "B"))
        results.append((yield from await_task(tid_a)))
        results.append((yield from await_task(tid_b)))

    start = time.perf_counter()
    run(main())
    elapsed = time.perf_counter() - start

    assert results == ["A", "B"]
    assert elapsed < 0.18, f"parallel await должен быть ~0.1s, а был {elapsed:.2f}s"


def test_await_wakes_in_order_of_completion() -> None:
    """B (delay=0.05) должен разбудить main раньше A (delay=0.2)."""

    def fetch(delay: float, name: str) -> Task:
        yield from sleep(delay)
        return name

    order: list[str] = []

    def main() -> Task:
        tid_a = create_task(fetch(0.2, "A"))
        tid_b = create_task(fetch(0.05, "B"))
        # awaits pending: await B (закончится первый), потом await A.
        b = yield from await_task(tid_b)
        order.append(b)
        a = yield from await_task(tid_a)
        order.append(a)

    run(main())
    assert order == ["B", "A"]


def test_await_already_finished_returns_immediately() -> None:
    """Если task завершилась ДО await'а, результат возвращается сразу
    из results-cache, без блокировки."""

    def quick() -> Task:
        return "done"
        yield  # unreachable, но нужен чтобы функция была generator

    def main() -> Task:
        tid = create_task(quick())
        # даём quick() шанс завершиться до нашего await'а
        yield from sleep(0.05)
        # теперь его result уже в scheduler'е
        result = yield from await_task(tid)
        assert result == "done"

    run(main())


def test_multiple_waiters_on_same_task() -> None:
    """N task'ей await'ят одну и ту же task'у - все получают результат."""

    def source() -> Task:
        yield from sleep(0.05)
        return 42

    got: list[int] = []

    def waiter() -> Task:
        val = yield from await_task(source_tid)
        got.append(val)

    source_tid = -1  # заполним в main

    def main() -> Task:
        nonlocal source_tid
        source_tid = create_task(source())
        w1 = create_task(waiter())
        w2 = create_task(waiter())
        w3 = create_task(waiter())
        yield from await_task(w1)
        yield from await_task(w2)
        yield from await_task(w3)

    run(main())
    assert got == [42, 42, 42]


def test_deadlock_detection() -> None:
    """Если task ждёт tid'а которого нет и не запланирован - deadlock."""

    def main() -> Task:
        # await'им несуществующего tid'а - scheduler повесится, но должен
        # обнаружить deadlock и raise'нуть.
        yield from await_task(999)

    with pytest.raises(RuntimeError, match="deadlock"):
        run(main())


def test_await_chain() -> None:
    """A await'ит B, B await'ит C. Результат течёт через цепочку."""

    def c() -> Task:
        yield from sleep(0.02)
        return "C"

    def b(c_tid: int) -> Task:
        val = yield from await_task(c_tid)
        return f"B->{val}"

    def a(b_tid: int) -> Task:
        val = yield from await_task(b_tid)
        return f"A->{val}"

    result_holder: list[str] = []

    def main() -> Task:
        c_tid = create_task(c())
        b_tid = create_task(b(c_tid))
        a_tid = create_task(a(b_tid))
        result_holder.append((yield from await_task(a_tid)))

    run(main())
    assert result_holder == ["A->B->C"]
