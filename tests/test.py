from algorithms.core import bubble_sort, insertion_sort, merge_sort

# Small example test array
A = [5, 2, 4, 6, 1, 3]


def test_insertion_sort_small() -> None:
    assert insertion_sort(A.copy(), len(A)) == [1, 2, 3, 4, 5, 6]


def test_bubble_sort_small() -> None:
    assert bubble_sort(A.copy(), len(A)) == [1, 2, 3, 4, 5, 6]


def test_merge_sort_small() -> None:
    """Test merge sort with a small list."""
    B = [12, 3, 7, 14, 6, 11, 2]
    sorted_B = [2, 3, 6, 7, 11, 12, 14]
    list_to_sort = B.copy()
    merge_sort(list_to_sort, 0, len(list_to_sort) - 1)
    assert list_to_sort == sorted_B
