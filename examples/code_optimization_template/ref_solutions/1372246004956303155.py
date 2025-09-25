"""Code optimization example for OpenEvolve"""

# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        left = l1
        right = l2
        dummy = ListNode()
        curr = dummy
        
        carry = 0
        while left or right or carry!=0 :
            leftval = left.val if left else 0
            rightval = right.val if right else 0
            
            summ = leftval + rightval + carry
                
          
                
            left = left.next if left else None
            right = right.next if right else None
            
            carry = summ//10
            curr.next = ListNode(summ%10)
            curr = curr.next
        
        return dummy.next