"""Code optimization example for OpenEvolve"""

# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        cur = start_dummy = ListNode()        

        carry = 0
        while l1 or l2 or carry:
            # total = sum of digits + carry, start with just carry
            total = carry
            
            # add l1's digit to total
            if l1:
                total += l1.val
                l1 = l1.next
            
            # add l2's digit to total
            if l2:
                total += l2.val
                l2 = l2.next
            
            digit = total % 10
            carry = total // 10        

            new_node = ListNode(digit)
            cur.next = new_node
            cur = new_node
            
        return start_dummy.next


        