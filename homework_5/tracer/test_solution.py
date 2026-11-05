import threading

import pytest

from solution import tracer

# ============================================================
# Basic behavior — no recursion
# ============================================================


def test_returns_callable():
    @tracer
    def f():
        return 1

    assert callable(f)


def test_simple_call_output(capsys):
    @tracer
    def double(x):
        return x * 2

    result = double(5)

    assert result == 10
    out = capsys.readouterr().out
    assert out == "-> double(5)\n<- double(5) = 10\n"


def test_no_args(capsys):
    @tracer
    def f():
        return 42

    f()
    out = capsys.readouterr().out
    assert "-> f()" in out
    assert "<- f() = 42" in out


def test_none_return(capsys):
    @tracer
    def noop():
        pass

    result = noop()
    assert result is None
    out = capsys.readouterr().out
    assert "= None" in out


def test_string_args_use_repr(capsys):
    """Args must use repr (quoted), otherwise logs are ambiguous."""

    @tracer
    def echo(s):
        return s

    echo("hello")
    out = capsys.readouterr().out
    assert "-> echo('hello')" in out
    assert "<- echo('hello') = 'hello'" in out


def test_kwargs_printed(capsys):
    @tracer
    def f(a, b=10, c=20):
        return a + b + c

    f(1, b=2)
    out = capsys.readouterr().out
    assert "-> f(1, b=2)" in out
    # c was not passed, so it must not appear in the log
    assert "c=" not in out


def test_container_result(capsys):
    @tracer
    def make():
        return [1, 2, 3]

    make()
    out = capsys.readouterr().out
    assert "= [1, 2, 3]" in out


# ============================================================
# Recursion — exact output and indentation
# ============================================================


def test_factorial_exact_output(capsys):
    @tracer
    def fact(n):
        if n <= 1:
            return 1
        return n * fact(n - 1)

    assert fact(3) == 6
    out = capsys.readouterr().out
    lines = out.rstrip("\n").split("\n")
    assert lines == [
        "-> fact(3)",
        "  -> fact(2)",
        "    -> fact(1)",
        "    <- fact(1) = 1",
        "  <- fact(2) = 2",
        "<- fact(3) = 6",
    ]


def test_entry_and_exit_same_indent(capsys):
    """Entry and matching exit must share the same indentation."""

    @tracer
    def f(n):
        if n == 0:
            return 0
        return f(n - 1)

    f(3)
    out = capsys.readouterr().out
    lines = out.rstrip("\n").split("\n")
    entries = [l for l in lines if l.lstrip().startswith("->")]
    exits = [l for l in lines if l.lstrip().startswith("<-")]
    # entries are top-down, exits are bottom-up
    for e, x in zip(entries, reversed(exits)):
        assert len(e) - len(e.lstrip()) == len(x) - len(x.lstrip())


def test_indentation_multiple_of_unit(capsys):
    @tracer
    def f(n):
        if n == 0:
            return 0
        return f(n - 1)

    f(4)
    out = capsys.readouterr().out
    for line in out.rstrip("\n").split("\n"):
        indent = len(line) - len(line.lstrip())
        assert indent % 2 == 0


def test_depth_is_linear_in_recursion(capsys):
    """Depth of the deepest line equals n-1 (0-indexed levels)."""

    @tracer
    def f(n):
        if n == 0:
            return 0
        return f(n - 1)

    f(5)
    out = capsys.readouterr().out
    max_indent = max(len(l) - len(l.lstrip()) for l in out.rstrip("\n").split("\n"))
    # With indent="  " (2 spaces), 5 calls means max depth index 4 -> 8 spaces
    assert max_indent == 10


# ============================================================
# Exceptions
# ============================================================


def test_exception_top_level(capsys):
    @tracer
    def boom():
        raise RuntimeError("oops")

    with pytest.raises(RuntimeError, match="oops"):
        boom()
    out = capsys.readouterr().out
    lines = out.rstrip("\n").split("\n")
    assert lines == [
        "-> boom()",
        "!! boom raised RuntimeError: oops",
    ]


def test_exception_in_recursion_propagates(capsys):
    @tracer
    def rec(n):
        if n == 0:
            raise ValueError("bottom")
        return rec(n - 1)

    with pytest.raises(ValueError, match="bottom"):
        rec(2)
    out = capsys.readouterr().out
    lines = out.rstrip("\n").split("\n")
    entries = [l for l in lines if l.lstrip().startswith("->")]
    raises = [l for l in lines if "raised" in l]
    assert len(entries) == 3
    assert len(raises) == 3


def test_depth_reset_after_exception(capsys):
    """After an exception, the next call starts at depth 0."""

    @tracer
    def f(n):
        if n > 0:
            raise RuntimeError("fail")
        return n

    with pytest.raises(RuntimeError):
        f(1)
    capsys.readouterr()  # discard

    result = f(0)
    assert result == 0
    out = capsys.readouterr().out
    first_line = out.split("\n")[0]
    assert first_line == "-> f(0)"  # no indentation


# ============================================================
# Mutual recursion — the main reason to use ContextVar
# ============================================================


def test_mutual_recursion_indentation(capsys):
    @tracer
    def is_even(n):
        if n == 0:
            return True
        return is_odd(n - 1)

    @tracer
    def is_odd(n):
        if n == 0:
            return False
        return is_even(n - 1)

    assert is_even(3) is False
    out = capsys.readouterr().out
    lines = out.rstrip("\n").split("\n")
    # 4 nested calls: is_even(3), is_odd(2), is_even(1), is_odd(0)
    assert lines[0] == "-> is_even(3)"
    assert lines[1] == "  -> is_odd(2)"
    assert lines[2] == "    -> is_even(1)"
    assert lines[3] == "      -> is_odd(0)"


def test_mutual_recursion_depth_shared(capsys):
    """
    Two different decorated functions must share the same depth counter.
    If each had its own counter, indentation would reset at every switch.
    """

    @tracer
    def a(n):
        if n == 0:
            return 0
        return b(n - 1)

    @tracer
    def b(n):
        if n == 0:
            return 0
        return a(n - 1)

    a(3)
    out = capsys.readouterr().out
    lines = out.rstrip("\n").split("\n")
    # Depths must be 0, 2, 4, 6 spaces (each level += 2)
    depths = [len(l) - len(l.lstrip()) for l in lines]
    assert depths == [0, 2, 4, 6, 6, 4, 2, 0]


# ============================================================
# functools.wraps metadata
# ============================================================


def test_metadata_preserved():
    @tracer
    def my_func(x):
        """Some docstring."""
        return x

    assert my_func.__name__ == "my_func"
    assert my_func.__doc__ == "Some docstring."
    assert hasattr(my_func, "__wrapped__")
    assert my_func.__wrapped__(5) == 5


# ============================================================
# Depth does not leak between independent calls
# ============================================================


def test_depth_does_not_accumulate(capsys):
    @tracer
    def f(n):
        if n == 0:
            return 0
        return f(n - 1)

    f(3)
    capsys.readouterr()
    f(2)
    out = capsys.readouterr().out
    assert out.split("\n")[0] == "-> f(2)"


def test_called_from_plain_function(capsys):
    """Non-decorated callers must not affect the depth."""

    @tracer
    def f():
        return 1

    def caller():
        return f()

    caller()
    out = capsys.readouterr().out
    assert out.startswith("-> f()")


# ============================================================
# Thread isolation — ContextVar guarantee
# ============================================================


def test_threads_do_not_share_depth(capfd):
    """
    Two threads, each doing a recursive call, must each start at depth 0.
    With a plain global, one thread's indentation would leak into the other.
    """

    @tracer
    def f(n):
        if n == 0:
            return 0
        return f(n - 1)

    barrier = threading.Barrier(2)
    errors = []

    def worker():
        try:
            barrier.wait()
            f(2)
        except BaseException as e:
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors
    out = capfd.readouterr().out

    # print() is not atomic across threads: two calls may share a line.
    # So count substrings, not lines.
    assert out.count("-> f(2)") == 2

    # Neither thread started at nonzero depth. If depth leaked between
    # threads (e.g. with a plain global), one of them would print
    # "  -> f(2)" (2 spaces) instead of "-> f(2)".
    assert "  -> f(2)" not in out
    assert "    -> f(2)" not in out


if __name__ == "__main__":
    pytest.main()
