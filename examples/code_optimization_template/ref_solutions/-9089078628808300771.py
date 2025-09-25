"""Code optimization example for OpenEvolve"""

# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:

        head = None
        curr = ListNode()
        carry = 0

        while l1 or l2 or carry:
            
            val1 = l1.val if l1 else 0
            val2 = l2.val if l2 else 0

            rslt =  carry + val1 + val2 
            digit = rslt % 10
            carry = rslt // 10

            nxt_node = ListNode(digit)
            curr.next = nxt_node
            curr = curr.next

            if not head:
                head = curr

            l1 = l1.next if l1 else None
            l2 = l2.next if l2 else None


        return head




            
        