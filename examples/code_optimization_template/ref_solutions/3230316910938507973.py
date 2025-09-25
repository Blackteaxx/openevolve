"""Code optimization example for OpenEvolve"""

# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        """
        dummyhead = ListNode(0)
        dummy = dummyhead
        carry = 0
        while l1 and l2:
            sum = l1.val + l2.val + carry 
            res = (sum)%10
            carry = (sum)//10

            dummy.next = ListNode(res)
            dummy = dummy.next

            l1 = l1.next
            l2 = l2.next
        
        while l1:
            sum = l1.val + carry
            res = sum%10
            carry = sum//10
            dummy.next = ListNode(res)
            l1 = l1.next
            dummy = dummy.next 
        
        while l2:
            sum = l2.val + carry
            res = sum%10
            carry = sum//10
            dummy.next = ListNode(res)
            l2 = l2.next
            dummy = dummy.next 

        if carry != 0:
            dummy.next = ListNode(carry)

        return dummyhead.next
        """
        dummyHead = dummy = ListNode(0)
        carry = 0

        while l1 or l2:
            v1, v2 = 0,0
            if l1:
                v1 = l1.val
                l1 = l1.next
            if l2:
                v2 = l2.val
                l2 = l2.next
            
            val = v1 + v2 + carry
            dummy.next = ListNode(val%10)
            dummy = dummy.next
            carry = val//10

        if carry:
            dummy.next = ListNode(carry)

        return dummyHead.next

        while l1:
            sum = l1.val


            
        