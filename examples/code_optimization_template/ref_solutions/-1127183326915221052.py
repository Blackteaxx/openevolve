"""Code optimization example for OpenEvolve"""

# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        carry = 0 
        dummy = temp = ListNode(0)
        while l1 or l2 or carry:
            l1_val = l1.val if l1 else 0
            l2_val = l2.val if l2 else 0

            res = l1_val + l2_val + carry
            if res >= 10:
                carry = 1
                new = ListNode(res % 10)
            else:
                carry = 0
                new = ListNode(res)
            temp.next = new
            temp = temp.next
            l1 = l1.next if l1 else None
            l2 = l2.next if l2 else None
        return dummy.next