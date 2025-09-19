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
        used = [[False] * n for _ in range(m)]
        for i in range(m):
            for j in range(n):
                if self.find(board, i, j, used, word):
                    return True
        return False

    def find(self, board, i, j, used, word):
        if not word: return True
        if i < 0 or i >= len(board) or j < 0 or j >= len(board[0]): return False
        if used[i][j] or board[i][j] != word[0]: return False
        used[i][j] = True
        found = self.find(board, i-1, j, used, word[1:]) or \
                self.find(board, i+1, j, used, word[1:]) or \
                self.find(board, i, j-1, used, word[1:]) or \
                self.find(board, i, j+1, used, word[1:])
        used[i][j] = False
        return found