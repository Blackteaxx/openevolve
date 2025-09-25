"""Code optimization example for OpenEvolve"""

# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
class Solution:
    def addTwoNumbers(self, l1: ListNode, l2: ListNode) -> ListNode:
               
        emptyHead=ListNode()
        emptyHead.next=ListNode()
        #t1=l1
        #t2=l2

        r=emptyHead
        
        cashe=0
        
        while l1 != None or l2 !=None or cashe>0:
              
            v1=l1.val if l1 else 0
            v2=l2.val if l2 else 0
            
            l1=l1.next if l1 and l1.next else None
            l2=l2.next if l2 and l2.next else None

            sum=v1+v2+cashe
            cashe=0        
            
            if sum>9:
                r.next=ListNode(val=sum-10)
                cashe+=1
                
            else:
                r.next=ListNode(val=sum)  
            r=r.next
            
                   
        
        
        return emptyHead.next
        