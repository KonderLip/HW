"""Сравнение цен в магазинах через asyncio. Условие — в README.md."""

import asyncio

# "База" магазинов: цена и время ответа API в секундах. НЕ менять.
PRICES: dict[str, int] = {"ozon": 990, "wb": 950, "yandex": 1100, "slow_shop": 900}
DELAYS: dict[str, float] = {"ozon": 0.3, "wb": 0.2, "yandex": 0.4, "slow_shop": 5.0}


async def fetch_price(shop: str) -> int:
    """Имитирует запрос к API магазина. НЕ менять.

    Неизвестный магазин отвечает за 0.1 с и возвращает цену 1000.
    """
    await asyncio.sleep(DELAYS.get(shop, 0.1))
    return PRICES.get(shop, 1000)


# ---------- Задача 1.1 ----------


async def get_prices_sequential(shops: list[str]) -> list[int]:
    """Запросить цены по очереди: следующий запрос — только после предыдущего.

    Подсказка: обычный цикл for и await fetch_price(...) внутри.
    """
    raise NotImplementedError


# ---------- Задача 1.2 ----------


async def get_prices_concurrent(shops: list[str]) -> list[int]:
    """Запросить цены одновременно. Порядок цен = порядок магазинов.

    Подсказка: asyncio.gather.
    """
    raise NotImplementedError


# ---------- Задача 1.3 ----------


async def get_price_or_none(shop: str, timeout: float = 1.0) -> int | None:
    """Цена магазина или None, если он не ответил за timeout секунд.

    Подсказка: asyncio.wait_for и except TimeoutError.
    """
    raise NotImplementedError


async def get_prices_with_timeout(shops: list[str], timeout: float = 1.0) -> list[int | None]:
    """Как get_prices_concurrent, но медленные магазины дают None, а не тормозят всех.

    Подсказка: gather по get_price_or_none.
    """
    raise NotImplementedError


# ---------- Задача 1.4 (дополнительная) ----------


async def get_prices_limited(shops: list[str], limit: int = 3) -> list[int]:
    """Запросить цены одновременно, но не больше limit запросов в один момент.

    Подсказка: asyncio.Semaphore(limit) и async with внутри вспомогательной функции.
    """
    raise NotImplementedError


if __name__ == "__main__":
    import time

    async def main() -> None:
        shops = ["ozon", "wb", "yandex"]
        for fn in (get_prices_sequential, get_prices_concurrent):
            start = time.perf_counter()
            result = await fn(shops)
            print(f"{fn.__name__:25} {time.perf_counter() - start:.2f}s  {result}")

        start = time.perf_counter()
        result_with_timeout = await get_prices_with_timeout(shops + ["slow_shop"])
        print(f"{'get_prices_with_timeout':25} {time.perf_counter() - start:.2f}s  {result_with_timeout}")

    asyncio.run(main())
