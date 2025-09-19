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
        def search_from(i,j):
            dirs = [(-1, 0), (1, 0), (0, 1), (0,-1)]
            starting = set()
            starting.add((i,j))
            stack = [(i,j,0, starting)]
            while len(stack) != 0:
                ati, atj, atletter, atvis = stack.pop()
                if atletter == len(word) - 1 and board[ati][atj] == word[-1]:
                    return True
                for d in dirs:
                    nexti = ati+d[0]
                    nextj = atj+d[1]
                    nextletter = atletter+1
                    if 0 <= nexti < len(board) and 0 <= nextj < len(board[0]) and (nexti, nextj) not in atvis and board[nexti][nextj] == word[nextletter]:
                        if nextletter == len(word) - 1:
                            return True
                        visited = atvis.copy()
                        visited.add((nexti, nextj))
                        stack.append((nexti, nextj, nextletter, visited))
            return False
        for i in range(len(board)):
            for j in range(len(board[0])):
                if board[i][j] == word[0] and search_from(i,j):
                    return True
        return False