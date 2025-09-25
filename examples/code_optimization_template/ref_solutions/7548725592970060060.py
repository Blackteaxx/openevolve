"""Code optimization example for OpenEvolve"""

# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        dummy_head = ListNode()
        current = dummy_head
        carry = 0

        while l1 or l2 or carry:
            # Extract digits from each list
            x = l1.val if l1 else 0
            y = l2.val if l2 else 0

            # Calculate the sum and carry
            _sum = x + y + carry
            carry = _sum // 10

            # Create a new node with the current digit
            current.next = ListNode(_sum % 10)
            current = current.next

            # Move to the next nodes in the input lists if available
            if l1:
                l1 = l1.next
            if l2:
                l2 = l2.next

        return dummy_head.next