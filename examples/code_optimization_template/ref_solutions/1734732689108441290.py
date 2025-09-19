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
        def dfs(ind, i, j):
            if self.found:
                return
            if ind == k:
                self.found = True
                return True

            dirs = [[0,1],[1,0],[0,-1],[-1,0]]
            if i < 0 or i >= len(board) or j < 0 or j >= len(board[0]) or board[i][j] != word[ind]:
                return False

            tmp = board[i][j]
            board[i][j] = "#"
            
            for iv, jv in dirs:
                di = i+iv
                dj = j+jv
                dfs(ind + 1,di, dj)
            board[i][j] = tmp

        m, n, k = len(board), len(board[0]), len(word)
        self.found = False
        chars = set()
        for i in range(m):
            for j in range(n):
                chars.add(board[i][j])
        for c in word:
            if c not in chars:
                return False


        for i in range(m):
            for j in range(n):
                if self.found:
                    return True
                dfs(0, i, j)
        
        return self.found