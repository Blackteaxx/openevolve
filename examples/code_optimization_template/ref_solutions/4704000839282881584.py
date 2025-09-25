"""Code optimization example for OpenEvolve"""

# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        if l1 == None:
            return l2
        if l2 == None:
            return l1
        
        p1 = l1
        p2 = l2
        carry = 0
        res = ListNode()
        head = res
        while p1 != None or p2 != None or carry != 0:
            v1 = 0 if p1 == None else p1.val
            v2 = 0 if p2 == None else p2.val

            val = v1 + v2 + carry
            carry = val // 10
            val = val % 10

            res.next = ListNode(val)
            res = res.next

            if p1 != None: p1 = p1.next
            if p2 != None: p2 = p2.next
        
        return head.next