# numeral.py

from .node import Node

class Numeral(Node):
    '''
    For \arabic{chapter} etc
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




