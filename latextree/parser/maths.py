# mathmode.py
'''
Flags such as noexpand and strict_braces stc are currently passed
anonomously via kwargs through the recursive calls to parse_tokens().
1. They could be defined explicitly in the parse_tokens() function definition ...
2. ... or we could use global variables?!

noexpand=True is implemented during parse_tokens, when characters 
(catcode 11 and 12) are appended to the running `chars` list:

    # check kwargs
    if 'noexpand' in kwargs and kwargs['noexpand']:
        chars.append(t.chars())
        continue

It would be better done by passing noexpand (via kwargs) to node.chars() 
on nodes of the specified type (e.g. verbatim or displaymath)
'''

from .node import Node
from .group import Group
from .command import Command, Environment


class Inline(Group):
    r'''
    Latex inline maths node. 
    To represent $ ... $ and \( ... \)
    We can also use \begin{math} ... \end{math}
    This is an inline environment!!
    '''
    def __init__(self, delimiter='tex'):
        Group.__init__(self)
        self.delimiter = delimiter
        self.pre_space  = '' # space after \( or \[
        self.post_space = '' # space after \) or \]
    
    def __repr__(self):
        # return '{}:{}:{}(delim=\'{}\')'.format(self.family, self.genus, self.species, self.delimiter)
        return '{}:{}(delim=\'{}\')'.format(self.genus, self.species, self.delimiter)

    # chars: restore delimiters
    def chars(self, **kwargs):
        s = []
        for child in self.children:
            s.append(child.chars())
        s = ''.join(s)

        if 'non_breaking_spaces' in kwargs and kwargs['non_breaking_spaces']:
            s = s.replace(' ', '~')
            s = s.replace('\n', '~')

        if self.delimiter == 'latex' or ('delim' in kwargs and kwargs['delim'] == 'latex'):
            return('\\(' + self.pre_space + s + '\\)' + self.post_space)
        return('${}$'.format(s)) 


class MathEnv(Environment):
    r'''
    Abstract class for mathmode environments.
    This is needed to make sure that Display objects (defined below) 
    have attribute node.family = 'Environment' which is useful
    in templates for HTML output. 
    '''
    def __init__(self, delimiter='tex'):
        Environment.__init__(self)
        self.delimiter = delimiter

class Display(MathEnv):
    r'''
    Latex displaymath node to represent $$ ... $$ and \[ ... \]
    Other display environments for mathematics have their own names:
        \begin{displaymath} ... \end{displaymath} (wrapper for the above)
        \begin{gather} ... \end{gather}
        \begin{equation} ... \end{equation} etc.
    These are created from .by the class factory from .defnitions. 
    Note that mathmode=True inside these environments, False outside
    There are also environments such as `array` and `cases` which can 
    only be used inside InlineMaths or DisplayMaths objects.
    '''
    def __init__(self, delimiter='tex'):
        MathEnv.__init__(self)
        self.delimiter = delimiter

    def __repr__(self):
        # return '{}:{}:{}(delim=\'{}\')'.format(self.family, self.genus, self.species, self.delimiter)
        return '{}:{}(delim=\'{}\')'.format(self.genus, self.species, self.delimiter)

    # chars: restore delimiters $$ ... $$ or \[ ... \]
    def chars(self, **kwargs):
        s = []
        for child in self.children:
            s.append(child.chars())
        s = ''.join(s)

        if 'non_breaking_spaces' in kwargs and kwargs['non_breaking_spaces']:
            s = s.replace(' ', '~')
            s = s.replace('\n', '~')

        if self.delimiter == 'latex' or ('strict_mathmode_delimiters' in kwargs and kwargs['strict_mathmode_delimiters']):
            return('\\[' + self.pre_space + s + '\\]' + self.post_space)
        return('$$' + self.pre_space + s + '$$' + self.post_space)





