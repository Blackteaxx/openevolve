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
        
        def dfs(y = 0, x = 0, i = 0, visited: Set[Tuple[int, int]] = set()):
            visited.add((y, x))
            # print(y, x, i)
            # print(board[y][x], word[i])
            # print(visited)
            if i == len(word) - 1: return True
            if board[y][x] != word[i]: return
            ad = self.adyacents(board, y, x)
            # options = filter(lambda op: op not in visited and board[op[0]][op[1]] == word[i + 1], ad)
            options = [op for op in ad if op not in visited and board[op[0]][op[1]] == word[i + 1]]
            some = False
            for op in options:
                y, x = op
                some = some or dfs(y, x, i + 1, visited.copy())
            return some
        
        for y, row in enumerate(board):
            for x, c in enumerate(row):
                if c == word[0]:
                    if dfs(y, x, 0, set()): return True

        return False

    def adyacents(self, arr: List[List], y: int, x: int) -> List[Tuple[int, int]]:
        res = []
        if y != 0: res.append((y - 1, x))
        if y != (len(arr) - 1): res.append((y + 1, x))
        if x != 0: res.append((y, x - 1))
        if x != (len(arr[y]) - 1): res.append((y, x + 1))
        return res