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
        dirs = [[0,1], [0,-1], [1,0], [-1, 0]]

        def f(idx, i, j):
            if idx == len(word):
                return True
            
            if i < 0 or i >= m or j < 0 or j >= n:
                return False
            
            if board[i][j] == "VIS":
                return False
            
            if board[i][j] != word[idx]:
                return False
            
            t = board[i][j]
            board[i][j] = "VIS"

            for d in dirs:
                upi = i + d[0]
                upj = j + d[1]
                if f(idx+1, upi, upj):
                    return True
            
            board[i][j] = t
            return False


        for i in range(m):
            for j in range(n):
                if board[i][j] == word[0] and f(0, i, j):
                    return True
        
        return False