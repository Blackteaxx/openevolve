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
        n = len(board)
        m = len(board[0])
        used_board = []
        for i in range(n):
            used_board.append([])
            for j in range(m):
                used_board[-1].append(False)
        flag=False
        
        def add_one(i:int, j:int, remain_word:str):
            #print("rem", remain_word, i,j)
            #print(used_board)
            nonlocal flag
            if remain_word=="":
                flag=True
                return

            if i>0 and board[i-1][j]==remain_word[0]:
                if used_board[i-1][j] == False:
                    used_board[i-1][j] = True
                    add_one(i-1,j,remain_word[1:])
                    used_board[i-1][j] = False
            if i<n-1 and board[i+1][j]==remain_word[0] and used_board[i+1][j] == False:
                used_board[i+1][j] = True
                add_one(i+1,j,remain_word[1:])
                used_board[i+1][j] = False
            if j>0 and board[i][j-1]==remain_word[0] and used_board[i][j-1] == False:
                used_board[i][j-1] = True
                add_one(i,j-1,remain_word[1:])
                used_board[i][j-1] = False
            if j<m-1 and board[i][j+1]==remain_word[0] and used_board[i][j+1] == False:
                used_board[i][j+1] = True
                add_one(i,j+1,remain_word[1:])
                used_board[i][j+1] = False


        for i in range(n):
            if flag:
                break
            for j in range(m):
                if flag:
                    break
                if board[i][j]!=word[0]:
                    continue
                used_board[i][j] = True
                add_one(i,j,word[1:])
                used_board[i][j] = False
        return flag