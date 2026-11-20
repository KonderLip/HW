"""Рассылка уведомлений пользователям. Условие — в README.md.

В этом коде есть ошибка: рассылка запускается через asyncio.gather,
но письма всё равно уходят по одному. Найдите и исправьте её.
"""

import asyncio
import time


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}")


async def render_template(user: str) -> str:
    """Собрать текст письма."""
    await asyncio.sleep(0.01)
    return f"Привет, {user}! У нас новые скидки."


async def send_email(user: str) -> str:
    """Отправить письмо одному пользователю (почтовый сервер отвечает ~0.5 с)."""
    text = await render_template(user)
    log(f"отправляю письмо {user}")
    time.sleep(0.5)  # ждём ответа почтового сервера
    log(f"письмо {user} доставлено")
    return f"{user}: {len(text)} символов"


async def notify_all(users: list[str]) -> list[str]:
    """Разослать письма всем пользователям одновременно."""
    return await asyncio.gather(*(send_email(user) for user in users))


if __name__ == "__main__":
    start = time.perf_counter()
    results = asyncio.run(notify_all(["anna", "boris", "vera", "gleb"]))
    print(results)
    print(f"Всего: {time.perf_counter() - start:.2f}s (ожидаем ~0.5 с)")
