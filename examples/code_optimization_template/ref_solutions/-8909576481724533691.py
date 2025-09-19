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

class Solution:
    def exist(self, board: List[List[str]], word: str) -> bool:
        m, n = len(board), len(board[0])
        def helper(i, r, c):
            if i >= len(word):
                return True
            
            if ((r < 0 or r >= m or c < 0 or c >= n) or
                board[r][c] == "#" or board[r][c] != word[i]):
                return False
            
            temp = board[r][c]
            board[r][c] = "#"
            res = (helper(i + 1, r, c - 1) or
                helper(i + 1, r, c + 1) or
                helper(i + 1, r - 1, c) or
                helper(i + 1, r + 1, c))
            board[r][c] = temp
            return res

        
        for r in range(m):
            for c in range(n):
                if helper(0, r, c):
                    return True
        return False