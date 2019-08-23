# tabular.py
'''
Catcode 4: Alignment character 
For environments such as tabular, tabbing, array, align, eqnarray, ...
    - the children of tabular are Row objects
    - the children of Row objects are Cell objects
Row could be subclassed from NodeList
Cell could be subclassed from Group

Row and Cell objects have the `format' attribute
    r.format = TTB means two hlines above and one below
    c.format = LLR means two vlines on the left and one on the right
'''
import logging
log = logging.getLogger(__name__)

logging.basicConfig(
    filename = 'latextree.log', 
    format = '%(levelname)8s:%(name)8s:%(funcName)20s:%(lineno)4s %(message)s',
    level = logging.DEBUG,
)

from .node import Node
from .command import Environment
from .tokens import Token
from .content import Text

class Cell(Node):
    def __init__(self):
        Node.__init__(self)
        self.format=''
    
    def chars(self, **kwargs):
        s = []
        for child in self.children:
            s.append(child.chars(**kwargs))
        return ''.join(s)


class Row(Node):
    def __init__(self):
        Node.__init__(self)
        self.format = ''

    def chars(self, **kwargs):
        s = []
        pre = ''
        post = ''
        for child in self.children:
            if child.species == 'Text': # captures newlines in the source code (not \\)
                pre += child.chars()
            elif child.species == 'hline':
                pre += child.chars()
            elif child.species == 'Backslash':
                post += child.chars()
            else:
                s.append(child.chars(**kwargs))

        return pre + '&'.join(s) + post

