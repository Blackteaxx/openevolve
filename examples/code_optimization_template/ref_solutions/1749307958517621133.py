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
        rows, cols = len(board), len(board[0])
        
        if rows * cols < len(word):
            return False

        boardCharFreq = defaultdict(int, sum(map(Counter, board), Counter()))
        wordCharFreq = defaultdict(int, sum(map(Counter, word), Counter()))

        for c, f in wordCharFreq.items():
            if c not in boardCharFreq or boardCharFreq[c] < f:
                return False

        def dfs(r, c, i):
            if i == len(word):
                return True
            if r < 0 or c < 0 or r == rows or c == cols or \
               word[i] != board[r][c]:
                return False

            board[r][c] = "#"

            res = dfs(r + 1, c, i + 1) or dfs(r - 1, c, i + 1) or \
                  dfs(r, c + 1, i + 1) or dfs(r, c - 1, i + 1)

            board[r][c] = word[i]
            return res

        for r in range(rows):
            for c in range(cols):
                if dfs(r, c, 0):
                    return True

        return False