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
        
        directions = [
            (0,-1),
            (1,0),
            (0,1),
            (-1,0),
        ]

        
        def recursiveExist(x, y, recursive_word, seen):
            
            if len(recursive_word) == 0:
                return True

            for (dx, dy) in directions:
                test_x, test_y = x + dx, y + dy
                if 0 <= test_x < len(board[0]) and 0 <= test_y < len(board) \
                and (test_x, test_y) not in seen and board[test_y][test_x] == recursive_word[0]:
                    if recursiveExist(test_x, test_y, recursive_word[1:], [*seen, (test_x, test_y)]):
                        return True

            return False

            
        for y, row in enumerate(board):
            for x, c in enumerate(row):
                if c == word[0] and recursiveExist(x,y,word[1:],[(x,y)]):
                    return True
                    
        return False