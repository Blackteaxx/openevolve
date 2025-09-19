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
    def exist(self, board: List[List[str]], word: str) -> bool:
        def dfs(r, c, word):
            if not word:
                return True
            
            temp, board[r][c] = board[r][c], '0'
            if r > 0 and board[r - 1][c] == word[0]:
                if dfs(r - 1, c, word[1:]):
                    return True
            if c > 0 and board[r][c - 1] == word[0]:
                if dfs(r, c - 1, word[1:]):
                    return True
            if r < len(board) - 1 and board[r + 1][c] == word[0]:
                if dfs(r + 1, c, word[1:]):
                    return True
            if c < len(board[0]) - 1 and board[r][c + 1] == word[0]:
                if dfs(r, c + 1, word[1:]):
                    return True

            board[r][c] = temp
            return False

        for r in range(len(board)):
            for c in range(len(board[0])):
                if board[r][c] == word[0]:
                    if dfs(r, c, word[1:]):
                        return True
        return False