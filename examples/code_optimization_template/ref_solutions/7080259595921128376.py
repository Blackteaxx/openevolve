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
        # count word
        d_word = {}
        for ch in word:
            if ch in d_word: d_word[ch] += 1
            else: d_word[ch] = 1

        # count board
        d = {}
        for row in range(len(board)):
            for col in range(len(board[0])):
                if board[row][col] not in d_word:
                    continue

                ch = board[row][col]
                if ch in d: d[ch].append((row, col))
                else: d[ch] = [(row, col)]

        if len(d_word) != len(d): return False

        # dfs
        if word[0] not in d: return False
        for row, col in d[word[0]].copy():
            # remove
            d[word[0]].remove((row, col))
            # dfs
            if self.dfs(row, col, word, 1, board, d): return True
            # add back
            d[word[0]].append((row, col))

        return False

    def dfs(self, row, col, word, index, board, d):
        if index >= len(word): return True
        
        for dr, dc in (0, 1), (0, -1), (-1, 0), (1, 0):
            nr, nc = row + dr, col + dc
            if 0 <= nr < len(board) and 0 <= nc < len(board[0]):
                if (nr, nc) not in d[word[index]]: continue

                d[word[index]].remove((nr, nc))
                if self.dfs(nr, nc, word, index+1, board, d):
                    return True
                d[word[index]].append((nr, nc))

        return False