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

        def dfs(x, y, suffix):
            if not suffix:
                return True
            
            direction = [(1,0),(-1,0),(0,1),(0,-1)]
            temp = board[x][y]
            board[x][y] = "#"
            for dx, dy in direction:
                newx = x + dx
                newy = y + dy
                if 0 <= newx < m and 0 <= newy < n and board[newx][newy] == suffix[0]:
                    if dfs(newx, newy, suffix[1:]):
                        return True
            
            board[x][y] = temp
            return False

        for i in range(m):
            for j in range(n):
                if board[i][j] == word[0]:
                    if dfs(i, j, word[1:]):
                        return True
        return False