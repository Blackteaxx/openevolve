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
        def dfs(r, c, i, visited):
            dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            
            if i >= len(word):
                return True

            if not(0 <= r < len(board) and 0 <= c < len(board[0])):
                return False
            if (r, c) in visited:
                return False

            if board[r][c] != word[i]:
                return False

            visited.add((r, c))
            for d in dirs:
                nr  = r + d[0]
                nc = c + d[1]
                if dfs(nr, nc, i + 1, visited):
                    return True

            visited.remove((r, c))

            return False
        
        for r in range(len(board)):
            for c in range(len(board[0])):
                if board[r][c] == word[0]:
                    if dfs(r, c, 0, set()):
                        return True
        return False