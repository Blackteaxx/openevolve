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
        
        # check all word letter in board
        grid_char = set()
        for i in range(len(board)):
            for j in range(len(board[0])):
                grid_char.add(board[i][j])
        for w in word:
            if w not in grid_char:
                return False

        def search(i, j, path):
            if len(path) == len(word):
                return path == word
            
            elif i < 0 or i >= len(board) or j<0 or j >= len(board[0]):
                return False

            elif board[i][j] == word[len(path)]:
                cur = word[len(path)]
                path += cur
                board[i][j] = "."
                for di, dj in [(0,-1), (0,1), (-1, 0), (1,0)]:
                   if search(i+di, j+dj, path): return True
                board[i][j] = cur
            else:
                return False


        for i in range(len(board)):
            for j in range(len(board[0])):
                if search(i, j, ""):
                    return True
        return False

        # grid_char = set()
        # for i in range(len(board)):
        #     for j in range(len(board[0])):
        #         grid_char.add(board[i][j])
        # for w in word:
        #     if w not in grid_char:
        #         return False

        # def track(a, b, cur):
        #     if len(cur) == len(word):
        #         return True
        #     elif a<0 or a >=len(board) or b<0 or b>=len(board[0]):
        #         return False
        #     elif board[a][b] == word[len(cur)]:
        #         board[a][b] = "#"
        #         cur += word[len(cur)]
        #         check =  track(a+1, b, cur) or track(a-1, b, cur) or track(a, b+1, cur) or track(a, b-1, cur)
        #         board[a][b] = cur[-1]
        #         return check
        #     else:
        #         return False

        # for i in range(len(board)):
        #     for j in range(len(board[0])):
        #         if track(i, j, ""):
        #             return True
        # return False