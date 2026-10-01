from typing import List


def main(strs: List[str]) -> List[List[str]]:
    groups = {}
    for s in strs:
        freq = {}
        for c in s:
            freq[c] = freq.get(c, 0) + 1
        key = frozenset(freq.items())
        try:
            groups[key].append(s)
        except KeyError:
            groups[key] = [s]
    return list(groups.values())


if __name__ == "__main__":
    print(main(["eat", "tea", "tan", "ate", "nat", "bat"]))
