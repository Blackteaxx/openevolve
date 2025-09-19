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
        m = len(board)
        n = len(board[0])

        def search(i, j, word):
            if not word: return True
            if i<0 or j<0 or i>=m or j>=n: return False
            if board[i][j] != word[0]: return False
            board[i][j] = '*'
            res = search(i+1, j, word[1:]) or search(i-1, j, word[1:]) or search(i, j+1, word[1:])or search(i, j-1, word[1:])
            board[i][j] = word[0]
            return res

        for i in range(m):
            for j in range(n):
                if board[i][j] == word[0]:
                    if search(i, j, word): return True

        return False