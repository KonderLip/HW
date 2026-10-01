from __future__ import annotations

import math
from typing import Any


class HashMap:
    """
    Hash map is an associative container that contains key-value pairs with unique keys.
    Search, insertion, and removal of elements have average constant-time complexity.
    A strategy of collision resolution is coalesced hashing with the cellar.
    """

    def __init__(self, hasher=None):
        """Default constructor creates no elements."""
        self._hasher = hasher if hasher is not None else hash
        self._data: list[_Data] = []
        self._element_count: int = 0
        self._primary_size: int = 0
        self._cellar_size: int = 0
        self._start_pos: int = 0
        # Current position in PRIMES.
        # Grows monotonically because rehash is only ever called with non-decreasing n.
        self._prime_idx: int = 0
        self._rehash(0)

    # ---------- Public interface ----------

    def size(self) -> int:
        """Returns the number of elements."""
        return self._element_count

    def empty(self) -> bool:
        """Checks whether the container is empty."""
        return self._element_count == 0

    def clear(self) -> None:
        """Clears the contents."""
        self._data = [_Data() for _ in range(self._primary_size + self._cellar_size)]
        self._element_count = 0
        self._start_pos = self._primary_size + self._cellar_size - 1

    def insert(self, key, value) -> None:
        """Inserts element. Does nothing if the key already exists."""
        h = self._hasher(key) % self._primary_size
        if self._find(key, h) == self.NONE:
            self._insert(key, value, h)

    def erase(self, key) -> bool:
        """Erases element. Returns True if the key was present."""
        pos = self._find(key, self._hasher(key) % self._primary_size)
        if pos == self.NONE:
            return False
        self._data[pos].used = False
        self._data[pos].deleted = True
        self._element_count -= 1
        return True

    def at(self, key):
        """Access specified element with bounds checking."""
        pos = self._find(key, self._hasher(key) % self._primary_size)
        if pos == self.NONE:
            raise KeyError(key)
        return self._data[pos].value

    def find(self, key, default=None):
        """Finds element with specific key. Returns default if not found."""
        pos = self._find(key, self._hasher(key) % self._primary_size)
        if pos == self.NONE:
            return default
        return self._data[pos].value

    def hash_function(self):
        """Returns function used to hash the keys."""
        return self._hasher

    def __contains__(self, key) -> bool:
        return self._find(key, self._hasher(key) % self._primary_size) != self.NONE

    def __len__(self) -> int:
        return self._element_count

    def __getitem__(self, key):
        return self.at(key)

    def __setitem__(self, key, value) -> None:
        h = self._hasher(key) % self._primary_size
        pos = self._find(key, h)
        if pos != self.NONE:
            self._data[pos].value = value
        else:
            self._insert(key, value, h)

    def __repr__(self) -> str:
        items = ", ".join(
            f"{self._data[p].key!r}: {self._data[p].value!r}"
            for p in range(len(self._data))
            if self._data[p].used
        )
        return f"HashMap({{{items}}})"

    # ---------- Private ----------

    def _find(self, key, pos: int) -> int:
        """Returns position of the key in the table or NONE, if it is not in it."""
        while True:
            if pos == self.NONE:
                return self.NONE
            slot = self._data[pos]
            if slot.used:
                if slot.key == key:
                    return pos
            elif not slot.deleted:
                return self.NONE
            # Using link.
            pos = slot.next

    def _insert(self, key, value, pos: int) -> int:
        """Inserts the key that doesn't exist and returns its position."""
        # If load factor is more than 0.5, then rehash the table.
        if (self._element_count << 1) > self._primary_size:
            self._rehash(self._primary_size << 1)
            pos = self._hasher(key) % self._primary_size

        if self._data[pos].used:
            distance = 0
            while self._data[pos].next != self.NONE and not self._data[pos].deleted:
                pos = self._data[pos].next
                distance += 1
            if self._data[pos].used:
                next_free = self._start_pos
                while self._data[next_free].used:
                    if next_free == 0:
                        next_free = self._primary_size + self._cellar_size - 1
                    else:
                        next_free -= 1
                    distance += 1
                    # If distance is more than max lookups, then immediately
                    # rehash the table. Load factor should be more than 0.25
                    # in case of a bad hash function.
                    if (self._element_count << 2) > self._primary_size and distance > self._max_lookups():
                        self._rehash(self._primary_size << 1)
                        return self._insert(
                            key, value, self._hasher(key) % self._primary_size
                        )
                self._start_pos = next_free
                self._data[pos].next = next_free
                pos = next_free

        slot = self._data[pos]
        slot.key = key
        slot.value = value
        slot.used = True
        slot.deleted = False
        # slot.next is intentionally preserved: if this was a tombstone in the
        # middle of a chain, we must keep the link to the rest of the chain.
        self._element_count += 1
        return pos

    def _next_prime(self, value: int) -> int:
        """Returns the next prime number from PRIMES, not less than value."""
        # Monotone pointer: total work across all rehashes is O(len(PRIMES)).
        while self.PRIMES[self._prime_idx] < value:
            self._prime_idx += 1
        return self.PRIMES[self._prime_idx]

    def _max_lookups(self) -> int:
        """Max lookups is log2 of primary_size."""
        return max(4, int(math.log2(self._primary_size)))

    def _rehash(self, n: int) -> None:
        """Rebuilds the table so that the primary_size is at least n."""
        old = [(s.key, s.value) for s in self._data if s.used]
        self._element_count = 0
        self._primary_size = self._next_prime(n)
        self._cellar_size = int(self._primary_size * self.B) + 1
        self._start_pos = self._primary_size + self._cellar_size - 1
        self._data = [_Data() for _ in range(self._primary_size + self._cellar_size)]
        for key, value in old:
            self._insert(key, value, self._hasher(key) % self._primary_size)

    # NONE is means there is no link to the next element in chain.
    NONE = -1

    # Let (cellar_size_ = B * primary_size_).
    # The article says that this is the optimal value.
    B = 7 / 43.0

    # Prime numbers for grow policy. The last is about 2^64.
    PRIMES = [
        2, 3, 5, 7, 11, 13, 17, 23, 29, 37, 47,
        59, 73, 97, 127, 151, 197, 251, 313, 397,
        499, 631, 797, 1009, 1259, 1597, 2011, 2539,
        3203, 4027, 5087, 6421, 8089, 10193, 12853, 16193,
        20399, 25717, 32401, 40823, 51437, 64811, 81649,
        102877, 129607, 163307, 205759, 259229, 326617,
        411527, 518509, 653267, 823117, 1037059, 1306601,
        1646237, 2074129, 2613229, 3292489, 4148279, 5226491,
        6584983, 8296553, 10453007, 13169977, 16593127, 20906033,
        26339969, 33186281, 41812097, 52679969, 66372617,
        83624237, 105359939, 132745199, 167248483, 210719881,
        265490441, 334496971, 421439783, 530980861, 668993977,
        842879579, 1061961721, 1337987929, 1685759167, 2123923447,
        2675975881, 3371518343, 4247846927, 5351951779, 6743036717,
        8495693897, 10703903591, 13486073473, 16991387857,
        21407807219, 26972146961, 33982775741, 42815614441,
        53944293929, 67965551447, 85631228929, 107888587883,
        135931102921, 171262457903, 215777175787, 271862205833,
        342524915839, 431554351609, 543724411781, 685049831731,
        863108703229, 1087448823553, 1370099663459, 1726217406467,
        2174897647073, 2740199326961, 3452434812973, 4349795294267,
        5480398654009, 6904869625999, 8699590588571, 10960797308051,
        13809739252051, 17399181177241, 21921594616111, 27619478504183,
        34798362354533, 43843189232363, 55238957008387, 69596724709081,
        87686378464759, 110477914016779, 139193449418173,
        175372756929481, 220955828033581, 278386898836457,
        350745513859007, 441911656067171, 556773797672909,
        701491027718027, 883823312134381, 1113547595345903,
        1402982055436147, 1767646624268779, 2227095190691797,
        2805964110872297, 3535293248537579, 4454190381383713,
        5611928221744609, 7070586497075177, 8908380762767489,
        11223856443489329, 14141172994150357, 17816761525534927,
        22447712886978529, 28282345988300791, 35633523051069991,
        44895425773957261, 56564691976601587, 71267046102139967,
        89790851547914507, 113129383953203213, 142534092204280003,
        179581703095829107, 226258767906406483, 285068184408560057,
        359163406191658253, 452517535812813007, 570136368817120201,
        718326812383316683, 905035071625626043, 1140272737634240411,
        1436653624766633509, 1810070143251252131, 2280545475268481167,
        2873307249533267101, 3620140286502504283, 4561090950536962147,
        5746614499066534157, 7240280573005008577, 9122181901073924329,
        11493228998133068689, 14480561146010017169, 18446744073709551557,
    ]


class _Data:
    """Information stored in a slot."""

    __slots__ = ("key", "value", "used", "deleted", "next")

    def __init__(self):
        self.key: Any = None
        self.value: Any = None
        self.used: bool = False
        self.deleted: bool = False
        self.next: int = HashMap.NONE
