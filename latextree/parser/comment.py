# comment.py

from .node import Node

class Comment(Node):
    '''
    Comment node. The comment character (%) and newline (\n) 
    These are stripped from the tex, but returned in chars(). 
    '''   
    def __init__(self, text=None):
        Node.__init__(self)
        self.comment = text

    def __repr__(self):
        # return '{}:{}({})'.format(self.genus, self.species, self.comment)
        return '{}:{}({})'.format(self.genus, self.species, self.comment)        


    def chars(self, **kwargs):
        return '%{}\n'.format(self.comment)

