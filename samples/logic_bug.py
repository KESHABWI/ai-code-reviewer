"""Duplicate detection and ordering checks for a list of transaction IDs."""


def find_duplicates(t):
    d = []
    for i in range(len(t)):
        for j in range(len(t)):
            if i != j and t[i] == t[j] and t[i] not in d:
                d.append(t[i])
    return d


def is_sorted_ascending(nums):
    for i in range(len(nums)):
        if nums[i] > nums[i + 1]:
            return False
    return True
