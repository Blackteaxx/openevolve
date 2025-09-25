"""Code optimization example for OpenEvolve"""

# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:

        carry = 0
        dummy_head = ListNode(0,None)
        
        current = dummy_head
        
        while carry or l1 or l2:
          
          total = 0
          if l1:
            total += l1.val
            l1 = l1.next
          if l2:
            total += l2.val
            l2 = l2.next
          
          res = (total + carry) % 10
          carry = (total + carry) // 10
          
          current.next = ListNode(res, None)
          current = current.next

        return dummy_head.next