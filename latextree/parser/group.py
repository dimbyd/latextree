# group.py

from .node import Node

class Group(Node):
    '''
    Catcodes 1 and 2
    Latex group node. 
    Should probably be subclassed from NodeList 
    '''
    def __init__(self):
        Node.__init__(self)
   
    def chars(self, nobrackets=False, **kwargs):
        s = []
        for child in self.children:
            s.append(child.chars())
        if nobrackets:
            return '{}'.format(''.join(s))
        return '{{{}}}'.format(''.join(s))




