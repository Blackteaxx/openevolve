"""Code optimization example for OpenEvolve"""

# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        ret = None
        p = ret
        p1 = l1
        p2 = l2
        carry = 0
        while True:
            if p1 == None and p2 == None:
                if num >= 10:
                    node = ListNode(1)
                    if ret == None:
                        ret = node
                        p = node
                    else:
                        p.next = node
                        p = node
                break
            val1 = p1.val if p1 != None else 0
            val2 = p2.val if p2 != None else 0
            num = val1 + val2 + carry
            if num >= 10:
                node = ListNode(num - 10)
                if ret == None:
                    ret = node
                    p = node
                else:
                    p.next = node
                    p = node
                carry = 1
            else:
                node = ListNode(num)
                if ret == None:
                    ret = node
                    p = node
                else:
                    p.next = node
                    p = node
                carry = 0
            p1 = p1.next if p1 != None else p1
            p2 = p2.next if p2 != None else p2
        return ret