"""Code optimization example for OpenEvolve"""

# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next


class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        
        remainder = 0
        n1 = 0
        n2 = 0

        # countPtr = l1
        # while countPtr:
        #     countPtr = countPtr.next
        #     n1 += 1

        # countPtr = l2
        # while countPtr:
        #     countPtr = countPtr.next
        #     n2 += 1

        firstPtr = l1
        secondPtr = l2

        result = ListNode()
        resHead = result

        while (firstPtr or secondPtr):
            val = remainder
            if firstPtr:
                val += firstPtr.val
                firstPtr = firstPtr.next
            
            if secondPtr:
                val += secondPtr.val
                secondPtr = secondPtr.next

            result.val = val % 10
            remainder = val//10

            if firstPtr or secondPtr:
                result.next = ListNode()
                result = result.next

        if remainder != 0:
            result.next = ListNode(remainder)

        return resHead