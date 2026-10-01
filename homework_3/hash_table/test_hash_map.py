import random
import time

import pytest

from hash_map import HashMap

# ----------------------------------------------------------- Basic tests


def test_empty():
    hm = HashMap()
    assert len(hm) == 0
    assert hm.empty()
    assert hm.find("x") is None
    assert "x" not in hm


def test_insert_find_erase():
    hm = HashMap()
    hm.insert("a", 1)
    hm.insert("b", 2)
    hm.insert("c", 3)

    assert hm.find("a") == 1
    assert hm.find("b") == 2
    assert hm.find("c") == 3
    assert hm.find("d") is None
    assert len(hm) == 3

    assert hm.erase("b") is True
    assert hm.erase("b") is False
    assert hm.find("b") is None
    assert len(hm) == 2


def test_insert_does_not_overwrite():
    """insert is idempotent for an existing key (matches std::unordered_map)."""
    hm = HashMap()
    hm.insert("k", 1)
    hm.insert("k", 2)
    assert hm.find("k") == 1


def test_setitem_overwrites():
    hm = HashMap()
    hm["k"] = 1
    hm["k"] = 2
    assert hm["k"] == 2


def test_at_raises_key_error():
    hm = HashMap()
    with pytest.raises(KeyError):
        hm.at("missing")


def test_contains_and_len():
    hm = HashMap()
    for i in range(50):
        hm.insert(i, i * i)
    assert len(hm) == 50
    for i in range(50):
        assert i in hm
        assert hm[i] == i * i
    assert 100 not in hm


def test_tombstone_reuse():
    """Erase every other key, then re-insert — chain links must survive."""
    hm = HashMap()
    for i in range(20):
        hm.insert(i, i)
    for i in range(0, 20, 2):
        hm.erase(i)
    for i in range(0, 20, 2):
        hm.insert(i, i * 100)

    for i in range(20):
        expected = i * 100 if i % 2 == 0 else i
        assert hm.find(i) == expected
    assert len(hm) == 20


def test_clear():
    hm = HashMap()
    for i in range(10):
        hm.insert(i, i)
    hm.clear()
    assert len(hm) == 0
    for i in range(10):
        assert hm.find(i) is None


def test_hash_function_exposed():
    def h(x):
        return 42

    hm = HashMap(hasher=h)
    assert hm.hash_function() is h


# ---------------------------------------------------- Random vs dict


_OPS = ["insert", "setitem", "find", "getitem", "erase", "contains"]


def _run_ops(hm, d, rng, n_ops, key_range):
    """Apply random ops to both containers and compare after each one."""
    for step in range(n_ops):
        op = rng.choice(_OPS)
        key = rng.randint(0, key_range)

        if op == "insert":
            val = rng.randint(0, 10**9)
            hm.insert(key, val)
            d.setdefault(key, val)
        elif op == "setitem":
            val = rng.randint(0, 10**9)
            hm[key] = val
            d[key] = val
        elif op == "find":
            assert hm.find(key) == d.get(key), f"step={step} op=find key={key}"
        elif op == "getitem":
            if key in d:
                assert hm[key] == d[key]
        elif op == "erase":
            got = hm.erase(key)
            expected = key in d
            assert got == expected, f"step={step} op=erase key={key}"
            if expected:
                del d[key]
        elif op == "contains":
            assert (key in hm) == (key in d)

        assert len(hm) == len(d), f"step={step} op={op}"


@pytest.mark.parametrize("seed", list(range(20)))
@pytest.mark.parametrize("n_ops", [50, 500, 5_000])
def test_random_vs_dict(seed, n_ops):
    rng = random.Random(seed)
    hm = HashMap()
    d = {}
    _run_ops(hm, d, rng, n_ops, key_range=max(20, n_ops // 2))


# --------------------------------------------------- Collisions / cellar


def _mod_hasher(mod):
    def h(x):
        return x % mod

    return h


@pytest.mark.parametrize("seed", list(range(10)))
@pytest.mark.parametrize("mod", [1, 2, 3, 5])
def test_collisions(seed, mod):
    """Force all keys into a few buckets to exercise chains and cellar."""
    rng = random.Random(seed)
    hm = HashMap(hasher=_mod_hasher(mod))
    d = {}
    _run_ops(hm, d, rng, 1_000, key_range=200)


@pytest.mark.parametrize("n", [10, 100, 1_000, 10_000])
def test_all_same_hash(n):
    """All keys collide into a single chain. Must still work correctly."""
    hm = HashMap(hasher=lambda x: 0)
    for i in range(n):
        hm.insert(i, i)
    assert len(hm) == n
    for i in range(n):
        assert hm.find(i) == i
    for i in range(0, n, 2):
        hm.erase(i)
    for i in range(n):
        if i % 2 == 0:
            assert hm.find(i) is None
        else:
            assert hm.find(i) == i


# ------------------------------------------------ Rehash invariants


def test_rehash_preserves_all():
    """Inserting enough to force multiple rehashes keeps everything."""
    hm = HashMap()
    for i in range(1_000):
        hm.insert(i, i * 7)
    for i in range(1_000):
        assert hm.find(i) == i * 7
    assert len(hm) == 1_000


def test_rehash_after_delete():
    hm = HashMap()
    for i in range(500):
        hm.insert(i, i)
    for i in range(0, 500, 2):
        hm.erase(i)
    # This pushes size past a rehash boundary in the presence of tombstones
    for i in range(500, 2_000):
        hm.insert(i, i)
    for i in range(500, 2_000):
        assert hm.find(i) == i
    for i in range(1, 500, 2):
        assert hm.find(i) == i
    for i in range(0, 500, 2):
        assert hm.find(i) is None


# ------------------------------------------------------- Timing bench


def _bench_hm(keys):
    hm = HashMap()
    t0 = time.perf_counter()
    for k in keys:
        hm[k] = k
    t1 = time.perf_counter()
    for k in keys:
        _ = hm[k]
    t2 = time.perf_counter()
    for k in keys:
        hm.erase(k)
    t3 = time.perf_counter()
    return t1 - t0, t2 - t1, t3 - t2


def _bench_dict(keys):
    d = {}
    t0 = time.perf_counter()
    for k in keys:
        d[k] = k
    t1 = time.perf_counter()
    for k in keys:
        _ = d[k]
    t2 = time.perf_counter()
    for k in keys:
        del d[k]
    t3 = time.perf_counter()
    return t1 - t0, t2 - t1, t3 - t2


@pytest.mark.parametrize("n", [1_000, 10_000, 100_000, 1_000_000])
def test_timing(n, capsys):
    rng = random.Random(0)
    keys = rng.sample(range(10**9), n)

    hm_ins, hm_find, hm_era = _bench_hm(keys)
    d_ins, d_find, d_era = _bench_dict(keys)

    with capsys.disabled():
        print(f"\n=== n = {n} ===")
        print(
            f"  insert: HashMap {hm_ins:8.4f}s   "
            f"dict {d_ins:8.4f}s   ratio {hm_ins / d_ins:6.2f}x"
        )
        print(
            f"  find:   HashMap {hm_find:8.4f}s   "
            f"dict {d_find:8.4f}s   ratio {hm_find / d_find:6.2f}x"
        )
        print(
            f"  erase:  HashMap {hm_era:8.4f}s   "
            f"dict {d_era:8.4f}s   ratio {hm_era / d_era:6.2f}x"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
