"""mini_asyncio: create_task / await поверх event loop'а на генераторах.

Задача: расширить мини-планировщик с лекции до маленького asyncio -
добавить `await_task(tid)`, чтобы task могла дождаться результата
другой task'и (аналог `result = await task` в реальном asyncio).
Условие - в README.md.

Что даётся:
- `Sleep` syscall, `sleep(duration)` helper (`yield from sleep(...)`).
- `Scheduler` с `create_task`, `run`, sleep-механикой.
- Global `_current` scheduler + публичный `create_task`/`run` API.

Точный контракт - в тестах.
"""

import time
from collections import deque
from collections.abc import Generator
from dataclasses import dataclass
from typing import Any

Task = Generator[Any, Any, Any]

# ---- Syscalls: единственные объекты уходящие наружу через yield ----


@dataclass
class Sleep:
    duration: float


# TODO


# ---- Scheduler + global "current running loop" ----

_current: "Scheduler | None" = None


class Scheduler:
    def __init__(self) -> None:
        # ready: (tid, task, send_value) - send_value отдаётся task.send()
        self.ready: deque[tuple[int, Task, Any]] = deque()
        self.sleeping: list[tuple[float, int, Task]] = []
        # TODO: state для waiters / results
        self.next_id = 0

    def _new_tid(self) -> int:
        self.next_id += 1
        return self.next_id

    def create_task(self, coro: Task) -> int:
        tid = self._new_tid()
        self.ready.append((tid, coro, None))
        return tid

    def run(self, main: Task) -> None:
        global _current  # noqa: PLW0603  # аналог asyncio._running_loop
        _current = self
        try:
            self.create_task(main)
            while self._has_work():
                self._wake_sleeping()
                if not self.ready:
                    self._idle_wait_or_deadlock()
                    continue
                self._step_one()
        finally:
            _current = None

    def _has_work(self) -> bool:
        # TODO
        return bool(self.ready or self.sleeping)

    def _wake_sleeping(self) -> None:
        now = time.monotonic()
        still: list[tuple[float, int, Task]] = []
        for wake_at, tid, task in self.sleeping:
            if wake_at <= now:
                self.ready.append((tid, task, None))
            else:
                still.append((wake_at, tid, task))
        self.sleeping = still

    def _idle_wait_or_deadlock(self) -> None:
        if self.sleeping:
            next_wake = min(w for w, _, _ in self.sleeping)
            time.sleep(max(0.0, next_wake - time.monotonic()))
        # TODO: deadlock detection

    def _step_one(self) -> None:
        tid, task, value = self.ready.popleft()
        try:
            syscall = task.send(value)
        except StopIteration as e:
            self._finish_task(tid, e.value)
            return
        self._handle_syscall(tid, task, syscall)

    def _finish_task(self, tid: int, result: Any) -> None:  # noqa: ANN401
        raise NotImplementedError

    def _handle_syscall(self, tid: int, task: Task, syscall: Any) -> None:  # noqa: ANN401
        if isinstance(syscall, Sleep):
            self.sleeping.append((time.monotonic() + syscall.duration, tid, task))
        # TODO: case для AwaitTask
        else:
            raise RuntimeError(f"unknown syscall: {syscall!r}")


# ---- Публичный API - имитируем asyncio ----


def sleep(duration: float) -> Task:
    """Аналог asyncio.sleep(). В user-коде: `yield from sleep(...)`."""
    yield Sleep(duration)


def create_task(coro: Task) -> int:
    """Аналог asyncio.create_task(). Синхронно (без yield) регистрирует
    coro в running loop'е, возвращает handle (tid)."""
    if _current is None:
        raise RuntimeError("нет running loop'а (вызывай из main через run())")  # noqa: RUF001
    return _current.create_task(coro)


# TODO: await_task(tid) helper
def await_task(tid: int) -> Task:
    raise NotImplementedError


def run(main: Task) -> None:
    """Аналог asyncio.run(). Создаёт scheduler, запускает main до завершения."""
    Scheduler().run(main)
