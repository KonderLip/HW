from typing import List

from homework_5.tracer.solution import tracer


def main(nums: List[int]) -> List[List[int]]:
    n = len(nums)
    result = []

    @tracer
    def backtrack(path: List[int], used: List[bool]) -> None:
        if len(path) == n:
            result.append(path.copy())
            return
        for i in range(n):
            if not used[i]:
                used[i] = True
                path.append(nums[i])
                backtrack(path, used)
                path.pop()
                used[i] = False

    backtrack([], [False] * n)
    return result


if __name__ == "__main__":
    print(main([1, 2, 3]))
    print(main([0, 1]))
    print(main([1]))
