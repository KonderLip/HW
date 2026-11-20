# Задача 3. Потокобезопасный LRU-кеш

Реализуйте класс `LRUCache[K, V]` — кеш фиксированной ёмкости, который
вытесняет ключ, к которому дольше всех не обращались (least recently used).
Такой кеш часто стоит перед медленной базой или внешним API, и к нему
одновременно обращаются несколько потоков веб-сервера.

```python
from thread_safe_lru import LRUCache

cache: LRUCache[str, int] = LRUCache(capacity=100)
cache.put("key", 42)
val = cache.get("key")                 # 42
missing = cache.get("no", default=-1)  # -1
size = len(cache)                      # int
"key" in cache                         # bool
```

Требования:

- `capacity >= 1`, иначе `ValueError` в `__init__`.
- `put(key, value)` вставляет или обновляет запись и делает ключ самым свежим.
- Если после вставки записей больше, чем `capacity`, удаляется самый старый ключ.
- `get(key)` при успехе тоже делает ключ самым свежим. Если ключа нет —
  возвращает `default` и порядок не трогает.
- `len(cache)` — текущий размер, `"key" in cache` — проверка наличия
  (порядок не трогает).
- Все методы потокобезопасны: одновременные вызовы из разных потоков не
  ломают кеш и не нарушают `len(cache) <= capacity`.

В `thread_safe_lru.py` уже есть заготовка с пошаговыми подсказками `TODO`
в каждом методе.

## Зачем здесь замок

Каждая операция кеша — это несколько шагов со словарём. Например, `put`
сначала записывает значение, потом проверяет размер и удаляет старый ключ.
Если два потока делают `put` в заполненный кеш одновременно, они могут
перемешать шаги и удалить лишний ключ или сломать внутреннюю структуру
`OrderedDict`. Поэтому каждый метод целиком выполняется под одним общим
замком `threading.RLock`.

## Как проверить

Нужен Python 3.12+ (в заготовке используется синтаксис `class LRUCache[K, V]`).
Из папки задачи:

```bash
pytest -v
```

## Материалы

- [`collections.OrderedDict`](https://docs.python.org/3/library/collections.html#ordereddict-objects) — методы `move_to_end` и `popitem(last=False)`
- [`threading.RLock`](https://docs.python.org/3/library/threading.html#rlock-objects)
