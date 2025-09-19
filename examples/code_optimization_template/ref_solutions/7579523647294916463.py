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
        #iterate row by row and try to build up the word
        #for each char record the count of missing chars. if seen before, ignore.
        def helper(i,j, w,s):
            if (i,j) in s:
                #print("already visited")
                return False
            else:
                s.add((i,j))
            #print(s)
            if w == None or w == '' or len(w) == 1:
                return True

            for x,y in [(1,0), (-1,0), (0,1), (0,-1)]:
                if  -1 < i+x < n_rows and -1 < j+y < n_cols:
                    if board[i+x][j+y] == w[1]:
                        #print(s)
                        if helper(i+x, j+y, w[1::],s) == True:
                            return True
                        #print(s)
            s.remove((i,j))
            return False
            
        if not board:
            return False
        n_rows = len(board)
        n_cols = len(board[0])

        for  i, row in enumerate(board):
            for j,letter in enumerate(row):
                if letter == word[0]:
                    s = set()
                    #print(i,j)
                    if helper(i, j, word, s) == True:
                        return True
        
        return False