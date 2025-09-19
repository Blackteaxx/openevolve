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
        word_counter = Counter(list(word))
        board_counter = None
        for b in board:
            if board_counter:
                board_counter += Counter(b)
            else:
                board_counter = Counter(b)
        for key in word_counter:
            if key not in board_counter or word_counter[key] > board_counter[key]:
                return False

            
        self.found = False
        def DFS(i,j,n,track):
            id = str((i,j))
            if i < 0 or i >= len(board) or j < 0 or j >= len(board[0]) or id in track or n > len(word) - 1 or self.found:                
                return 

            if word[n] == board[i][j]:                
                n += 1  
                track.append(id)              
                DFS(i,j + 1,n,track) #right     
                DFS(i + 1,j,n,track) #down           
                DFS(i,j - 1,n,track) #left
                DFS(i - 1,j,n,track) #up
                track.pop(-1)
                

            if n == len(word):
                self.found = True
                return  

            
        #track=[]
        for i in range(len(board)):
            for j in range(len(board[i])):
                DFS(i,j,0,[])
                if self.found:
                    return True
        return False