# content.py
r'''
Content nodes contain printable characters
All other nodes are structural/stylistic/etc
'''

from lxml import etree
from .node import Node

class Content(Node):

    def __init__(self):
        Node.__init__(self)
        self.content = ''
 
    def __repr__(self):
        # return '{}:{}:{}({})'.format(self.family, self.genus, self.species, self.content)
        return '{}:{}({})'.format(self.genus, self.species, self.content)


class Text(Content):
    '''
    Text class 
    Content node for printable characters, which is nearly everything!
    The only other types that appear on the page/screen are
        1. names (e.g. chaptername, abstractname, contentname, etc) TODO
        2. numbers (e.g. \arabic{chapter}.\arabic{equation})
    '''    
    def __init__(self, text=None):
        Content.__init__(self)
        self.content = text

    # strip traliing newlines (prettify)
    def __repr__(self):
        return '{}:{}({})'.format(self.genus, self.species, self.content.strip('\n'))

    def chars(self, **kwargs):
        return self.content

    def xml(self):
        elt = etree.Element(self.species)
        elt.text =  self.content.strip('\n') # strip for nice printing!!
        return elt


class Number(Content):
    '''
    Content node for integer types (set by counter values)
    Argument: `number`
    Typically used as the `value' attribute of a `Numeral' type
        e.g arabic, alph etc. 

    To represent numbers explicitly (instead of as strings) might be 
    useful with commands like \var{...} in problem sheets, to include
    different numbers each time (as used in Numbas)

    For `Numeral' commands e.g `\arabic{chapter}' 
    we set 
        node.args['counter'] = 'chapter'
        node.children = [Number(3),]
    
    So node.chars() expands correctly provided we ignore the children.
        - i.e. set noexpand=True for `Numeral' nodes
    
    Can we typeset the numeral in css?
        <arabic>3</arabic>
        <arabic value='3'>
        <number style='arabic>3</number>
        <number style='arabic, value='3'>
    
    Easier: via `set_number' implement
        node.number = Number(3)
        node.number_str = 'A.3'
    for every numbered (or numbered_like) species

    and every `Numeral' object has
        `value' field (integer)

    This means we need to have
    if self.species == 'arabic':
        return chr(97+self.value)
    '''    
    def __init__(self, value=None):
        Content.__init__(self)
        self.content = int(value)

    # strip traliing newlines (prettify)
    def __repr__(self):
        return '{}:{}({})'.format(self.genus, self.species, self.content)

    def chars(self, **kwargs):
        return ''

    def xml(self):
        elt = etree.Element(self.species)
        # elt.set('value', str(self.content))
        elt.text = str(self.content)
        return elt


