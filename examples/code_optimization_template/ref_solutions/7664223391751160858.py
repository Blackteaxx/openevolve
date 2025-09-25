"""Code optimization example for OpenEvolve"""

# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        dummy = answer = ListNode()
        s = 0
        while l1 and l2:
            s += l1.val + l2.val
            answer.next = ListNode(s%10)
            answer = answer.next
            s //= 10
            l1, l2 = l1.next, l2.next
        while l1:
            s += l1.val
            answer.next = ListNode(s%10)
            answer = answer.next
            s //= 10
            l1 = l1.next
        while l2:
            s += l2.val
            answer.next = ListNode(s%10)
            answer = answer.next
            s //= 10
            l2 = l2.next
        if s==1:
            answer.next = ListNode(1)
        return dummy.next