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
        search = set([])
        for r in range(len(board)): 
            for c in range(len(board[0])): 
                if board[r][c] == word[0]:
                    search.add((r, c))

        for r, c in search: 
            if self.dfs(board, word, r, c, 0):
                return True        
        return False

    def dfs(self, board, word, r, c, i):
            if r < 0 or r >= len(board) or c < 0 or c >= len(board[0]):
                return False 
            
            if board[r][c] != word[i]: 
                return False 
            if i == len(word) - 1:
                return True
            temp = board[r][c]
            board[r][c] = "None"
            ans = (self.dfs(board, word, r, c+1, i+1)
                    or self.dfs(board, word, r-1, c, i+1)
                    or self.dfs(board, word, r, c-1, i+1)
                    or self.dfs(board, word, r+1, c, i+1))
            board[r][c] = temp
            return ans