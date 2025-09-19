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
        # start = 0
        # recursive word search:
        #   given index, board, visited:
        #       if index is at the end of the word and current cell is the last character, true
        #       search every cell to the top, left, right, and down of current cell
        #       if next cell has same letter as next letter in word:
        #           add cell to visited, call index + 1, next cell, visited
        #       return true if any true else false

        m, n = len(board), len(board[0]) 

        def word_search_recursive(current_word_index, visited, current_cell):
            print()
            i, j = current_cell
            current_character = board[i][j]
            if current_word_index == (len(word) - 1):
                return current_character == word[current_word_index]

            elif current_character != word[current_word_index]:
                return False

            neighbor_results = list()

            for d_i, d_j in {(0, 1), (0, -1), (1, 0), (-1, 0)}:
                next_cell = (i + d_i, j + d_j)

                if next_cell[0] < 0 or next_cell[0] >= m: continue
                if next_cell[1] < 0 or next_cell[1] >= n: continue
                if next_cell in visited: continue

                visited.add(next_cell)
                if word_search_recursive(current_word_index + 1, visited, next_cell):
                    return True
                visited.remove(next_cell)

            return False


        for i in range(m):
            for j in range(n):
                start_i = int(0)
                visited = set({(i, j)})
                if not word_search_recursive(start_i, visited, (i, j)):
                    continue
                else:
                    return True
        
        return False