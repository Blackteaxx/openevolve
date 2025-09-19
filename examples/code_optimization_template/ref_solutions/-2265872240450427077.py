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
        letters_in_board = set()
        for i in range(len(board)):
            for j in range(len(board[0])):
                letters_in_board.add(board[i][j])
        
        for letter in word:
            if letter not in letters_in_board:
                return False


        def helper(coords, i, j, k):
            if k == len(word):
                return True
            
            if (i, j) in coords or i < 0 or j < 0 or i >= len(board) or j >= len(board[i]) or board[i][j] != word[k]:
                return False
            
            l = board[i][j]
            coords.add((i,j))
            flag1 = helper(coords, i+1, j, k+1)
            flag2 = helper(coords, i-1, j, k+1)
            flag3 = helper(coords, i, j+1, k+1)
            flag4 = helper(coords, i, j-1, k+1)
            
            coords.remove((i,j))

            return flag1 or flag2 or flag3 or flag4
                
        
        for i in range(len(board)):
            for j in range(len(board[i])):
                if helper(set(), i, j ,0):
                    return True
        return False