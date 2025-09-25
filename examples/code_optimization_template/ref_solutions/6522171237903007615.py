"""Code optimization example for OpenEvolve"""

# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
class ListNode(object):
    def __init__(self, x):
        self.val = x
        self.next = None

class Creator:

    def populate(self, in_list):
        # creating the head node
        curr = ListNode(in_list[0])
        head = curr
        # iterating over input list
        for i in in_list[1:]:
          temp = ListNode(i)
          curr.next = temp
          curr = temp

        return head
class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        l1a = []
        l2a = []
        while(True):
            l1a.append(l1.val)
            if(l1.next is None): #this is our do-while loop emulation, checking if this is the last Node
                break
            l1 = l1.next #update cur so we move on in the next iteration
        while(True):
            l2a.append(l2.val)
            if(l2.next is None): #this is our do-while loop emulation, checking if this is the last Node
                break
            l2 = l2.next #update cur so we move on in the next iteration
        l3a = []
        check = 0
        if (len(l1a) < len (l2a)):
            temp = l1a
            l1a = l2a
            l2a = temp
        if (len(l1a) >= len (l2a)):
            for i in range(len(l1a)):
                if (i<len(l2a)):
                    test = (l1a[i]+l2a[i]+ check)%10
                    l3a.append(test)
                    if ((l1a[i]+l2a[i]+ check)/10 >= 1):
                        check = 1
                    else:
                        check = 0
                else:
                    l3a.append((l1a[i]+check)%10)
                    if ((l1a[i]+check)>=10):
                        check = 1
                    else:
                        check = 0
        if (check==1):
            l3a.append(1)
        print(l3a)
        result = Creator().populate(l3a)
        return result