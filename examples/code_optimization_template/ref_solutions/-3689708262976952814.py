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
        # Count characters in board using defaultdict
        board_char_count = defaultdict(int)
        for row in board:
            for char in row:
                board_char_count[char] += 1

        # Count characters in word using defaultdict
        word_char_count = defaultdict(int)
        for char in word:
            word_char_count[char] += 1

        # Early Termination Check
        for char, count in word_char_count.items():
            if count > board_char_count[char]:
                return False

        # Decide whether to reverse the word
        first_char, last_char = word[0], word[-1]
        if board_char_count[last_char] < board_char_count[first_char]:
            word = word[::-1]  # Reverse the word

        def dfs(i, j, word_index):
            if word_index == len(word):
                return True
            if i < 0 or i >= len(board) or j < 0 or j >= len(board[0]):
                return False
            if board[i][j] != word[word_index]:
                return False
            
            temp = board[i][j] 
            board[i][j] = 'X'

            found = (dfs(i + 1, j, word_index + 1) or
                     dfs(i - 1, j, word_index + 1) or
                     dfs(i, j + 1, word_index + 1) or
                     dfs(i, j - 1, word_index + 1))

            board[i][j] = temp
            return found

        for i in range(len(board)):
            for j in range(len(board[0])):
                if dfs(i, j, 0):
                    return True

        return False