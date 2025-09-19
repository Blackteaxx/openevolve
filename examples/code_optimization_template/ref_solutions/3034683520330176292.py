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

# Start time 1:42pm
# End time: 1st submission 2:04

directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
class Solution:
    def exist(self, board: List[List[str]], word: str) -> bool:
        # iterate over each cell to start and check for the word
        word_found = False

        for row in range(len(board)):
            for col in range(len(board[0])):
                word_found = word_found or self.check_word(board, row, col, word, "", word_found)

        return word_found

    def check_word(self, board, row, col, word, current_word, word_already_found, visited = set()):
        if word_already_found:
            return word_already_found
        letter = board[row][col]
        if letter != word[len(current_word)]:
            return False
        new_word = current_word + letter
        word_found = False
        visited.add((row, col))
        if new_word == word:
            word_found = True
        else:
            for row_change, col_change in directions:
                new_row, new_col = (row_change + row, col_change + col)
                if self.valid_coordinate(len(board), len(board[0]), new_row, new_col) and (new_row, new_col) not in visited:
                    word_found = word_found or self.check_word(board, new_row, new_col, word, new_word, word_found, visited)
        visited.remove((row, col))

        return word_found

    def valid_coordinate(self, row_limit, col_limit, row, col):
        return 0 <= row < row_limit and 0 <= col < col_limit