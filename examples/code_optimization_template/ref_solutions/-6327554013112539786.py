"""Code optimization example for OpenEvolve"""

# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        num1, num2 = "", ""
        while l1:
            num1 = num1 + str(l1.val)
            l1 = l1.next
        
        while l2:
            num2 = num2 + str(l2.val)
            l2 = l2.next
    
        num1 = num1[::-1]
        num2 = num2[::-1]

        num = str(int(num1) + int(num2))[::-1]


        # converting a list/str to Linkedlist..
        head = ListNode(-1)
        trav = head
        for n in num:
            trav.next = ListNode(int(n))
            trav = trav.next
        return head.next
        