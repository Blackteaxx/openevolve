# EVOLVE-BLOCK-START
"""Code optimization example for OpenEvolve"""
from typing import *
from bisect import *
from collections import *
from copy import *
from datetime import *
from heapq import *
from math import *
from re import *
from string import *
from random import *
from itertools import *
from functools import *
from operator import *

import string
import re
import datetime
import collections
import heapq
import bisect
import copy
import math
import random
import itertools
import functools
import operator


class TreeNode:
    def __init__(self, val=0, left=None, right=None, next=None):
        self.val = val
        self.left = left
        self.right = right
        self.next = next


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


from typing import List


class Solution:
    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:
        total_nums = nums1 + nums2
        return total_nums[len(total_nums) // 2]


# EVOLVE-BLOCK-END


# This part remains fixed (not evolved)
def test():
    solution = Solution()
    assert solution.findMedianSortedArrays([20, 67], [37, 85]) == 52.0
    assert solution.findMedianSortedArrays([1, 2, 13, 22, 34, 46, 63, 86], [59, 80]) == 40.0
    assert (
        solution.findMedianSortedArrays(
            [8, 57, 82, 87], [8, 18, 20, 23, 40, 41, 54, 63, 72, 93]
        )
        == 47.5
    )
    assert solution.findMedianSortedArrays([3, 36, 78], [13, 20, 28, 45, 59, 89]) == 36.0
    assert (
        solution.findMedianSortedArrays(
            [17, 34, 43, 48, 51, 53, 83, 88], [43, 48, 54, 78, 88]
        )
        == 51.0
    )
    assert (
        solution.findMedianSortedArrays(
            [21, 28, 53, 63, 94], [6, 9, 25, 27, 31, 55, 60, 67, 78]
        )
        == 42.0
    )
    assert (
        solution.findMedianSortedArrays([17, 50, 54], [1, 20, 46, 52, 53, 62, 63, 66, 70])
        == 52.5
    )
    assert (
        solution.findMedianSortedArrays([11, 13, 15, 27, 29, 55, 74, 89, 96], [9, 39, 72])
        == 34.0
    )
    assert (
        solution.findMedianSortedArrays(
            [21, 24, 26, 33, 50, 53, 68, 87, 100], [1, 6, 12, 14, 34, 64, 81, 92, 93]
        )
        == 42.0
    )
    assert (
        solution.findMedianSortedArrays(
            [12, 29, 31, 38, 45, 47, 73, 76, 89, 92], [2, 22, 57, 85]
        )
        == 46.0
    )
    assert (
        solution.findMedianSortedArrays([17, 25, 36, 41, 43, 58, 90], [27, 58, 75, 77, 86])
        == 50.5
    )
    assert solution.findMedianSortedArrays([24, 28, 71, 96], [2, 8, 9, 16, 21, 53]) == 22.5
    assert (
        solution.findMedianSortedArrays([9, 26, 32, 33, 36, 45, 56, 63], [66, 68]) == 40.5
    )
    assert (
        solution.findMedianSortedArrays(
            [6, 17, 22, 24, 27, 48, 74, 75, 88], [16, 31, 39, 41, 70]
        )
        == 35.0
    )
    assert (
        solution.findMedianSortedArrays([4, 16, 18, 20, 26, 48, 92, 97], [12, 41, 70, 90])
        == 33.5
    )
    assert (
        solution.findMedianSortedArrays([4, 6, 8, 11, 30, 36, 60, 76, 79, 88], [29, 45, 56])
        == 36.0
    )
    assert (
        solution.findMedianSortedArrays([21, 22, 55, 61, 70, 73, 97], [2, 16, 34, 53])
        == 53.0
    )
    assert (
        solution.findMedianSortedArrays([22, 44, 48, 98], [30, 32, 34, 50, 59, 62]) == 46.0
    )
    assert (
        solution.findMedianSortedArrays([3, 18, 31, 57, 100], [4, 8, 46, 69, 71, 81, 98])
        == 51.5
    )