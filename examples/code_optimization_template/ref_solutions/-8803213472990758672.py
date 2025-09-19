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
        rows = len(board)
        cols = len(board[0])
        word_count = Counter(word)
        for item in word_count.items():
            found = False
            for i in range(rows):
                if found:
                    break
                for j in range(cols):
                    if item[0] == board[i][j]:
                        found = True
                    if found:
                        break
            if found == False:
                return False
                
        self.length = len(board[0])
        self.width = len(board)
        for i in range(self.width):
            for j in range(self.length):
                print(i,j)
                if self.dfs(i,j,word,board):
                    return True
        return False

    def dfs(self,i,j,word,board):
        if len(word) == 0:
            return True
        if board[i][j] != word[0]:
            return False
        else:
            if len(word) == 1:
                return True
            board[i][j] = ''
            if i+1 < self.width and self.dfs(i+1, j, word[1:], board):
                return True
            elif j+1 < self.length and self.dfs(i, j+1, word[1:], board):
                return True
            elif i-1 >= 0 and self.dfs(i-1, j, word[1:], board):
                return True
            elif j-1 >= 0 and self.dfs(i, j-1, word[1:], board):
                return True
            else:
                board[i][j] = word[0]
                return False