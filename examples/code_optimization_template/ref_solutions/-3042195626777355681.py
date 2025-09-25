"""Code optimization example for OpenEvolve"""

# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        sum = ListNode()
        tul_l1=1
        tul_l2=1
        tmp=l1
        while tmp.next != None:
            tul_l1 += 1
            tmp=tmp.next
        tmp=l2
        while tmp.next != None:
            tul_l2 += 1
            tmp=tmp.next
        
        tul_max= tul_l1 if tul_l1>tul_l2 else tul_l2

        c=0
        cur_sum = sum
        for i in range(tul_max):
            i+=1
            a=0
            b=0
            if l1 != None:
                a = l1.val
            if l2 != None:
                b = l2.val

            cur_sum.next = ListNode((a+b+c)%10)

            if a+b+c>9 :
                c=1
            else:
                c=0
            cur_sum=cur_sum.next
            if l1.next != None:
                l1=l1.next
            else:
                l1=ListNode()
            if l2.next != None:
                l2=l2.next
            else:
                l2=ListNode()
        
        if c>0:
            cur_sum.next=ListNode(c)
        
        return sum.next

            
            
            







        
            


            












        