"""Code optimization example for OpenEvolve"""

# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:

        dummy = ListNode()
        cur = dummy
        carry = 0

        while l1 or l2 or carry:
            value = (l1.val if l1 else 0) + (l2.val if l2 else 0) + carry
            carry = value // 10
            value = value % 10
            new_node = ListNode(value)
            cur.next = new_node
            cur =  cur.next
            l1 = l1.next if l1 else None
            l2 = l2.next if l2 else None

        return dummy.next
