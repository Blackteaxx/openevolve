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
        self.n = len(board)
        self.m = len(board[0])

        for i in range(self.n):
            for j in range(self.m):
                if board[i][j] == word[0]:
                    if self.dfs(board,i,j,word,0):
                        return True
        return False
        
    def dfs(self,board,x,y,word,i):
        directions = {(1,0),(0,1),(0,-1),(-1,0)}
        if word[i] != board[x][y]:
            return False
        
        if i == len(word)-1:
            return True

        for dx, dy in directions:
            newx, newy = x + dx, y + dy
            if 0<=newx<self.n and 0<=newy<self.m and word[i] == board[x][y]:
                tmp = board[x][y]   
                board[x][y] = "#"
                if self.dfs(board,newx,newy,word,i+1):
                    return True
                board[x][y] = tmp   # thanks tmp
                      
        return False