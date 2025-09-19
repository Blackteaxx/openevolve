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
      for i in range(len(board)):
        for j in range(len(board[0])):
          if self.dfs(i,j, 0, board, word):
            return True
      return False
        

    

    def dfs(self, i, j, k, board, word):
      if i < 0 or j < 0 or j >= len(board[0]) or i >= len(board) or board[i][j] != word[k]:
        return False
      
      if k == len(word) - 1:
        return True
      
     
      for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
        tmp = board[i][j]
        board[i][j] = -1

        if self.dfs(i + dx, j + dy, k + 1, board, word):
          return True
        
        board[i][j] = tmp