import contextvars
import functools

_depth = contextvars.ContextVar("trace_depth", default=0)


def tracer(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        d = _depth.get()
        indent = "  " * d
        args_repr = ", ".join(
            [repr(a) for a in args] + [f"{k}={v!r}" for k, v in kwargs.items()]
        )
        print(f"{indent}-> {func.__name__}({args_repr})")
        token = _depth.set(d + 1)
        try:
            result = func(*args, **kwargs)
        except BaseException as e:
            _depth.reset(token)
            print(f"{indent}!! {func.__name__} raised {type(e).__name__}: {e}")
            raise
        _depth.reset(token)
        print(f"{indent}<- {func.__name__}({args_repr}) = {result!r}")
        return result

    return wrapper
