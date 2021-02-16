# parameters.py
r'''
Module for dealing with parameter definitions
    parameters are placeholders 
    arguments are the actual values

TeX has only mandatory arguments. These can be specified in several ways
        \textbf{hello}
        \textbf\LaTeX
        \textbf1
        \textbf A
 
An ArgTable object maps parameter names onto Node objects.
These Node objects can be one of three types:
    Group   for \textbf{hello}    # list of nodes
    OptArg  for \item[*]          # list of nodes
    Command   for \textbf\LaTeX   # single node    
    Text    for \textbf1          # single node    
    Text    for \textbf A         # single node    

The last three come by the TeX rule that "if the first non-space is not a left brace or
a left bracket, the next token is the argument". Thus if we expect a mandatory argument 
and/or the possibility of an optional argument and the next (non-space) token is neither, 
we just take the next token as the argument, convert to a LatexTree node of some kind, 
then assign this to the ArgTable agains the argument name (defined in coredefs.py)

This module defines the following:
1. Parameter    - named tuple with argument type (s|o|m) and argument name 
2. OptArg       - subclass of Node to represent an optional argument 
3. ArgTable     - ordered dict mapping parameter names to Node objects

ArgTable is an ordered dictionary so that we can reconstruct the source Latex correctly.

4. parse_definition
    - extracts command definitions from .coredefs.py in the form
        {'species_name': Parameter}
    - used as a lookup-table in parser.parse_arguments


'''
from collections import namedtuple, OrderedDict
from .content import Text, Number
from .group import Group
from .node import Node
from .tokens import Token
import json
from lxml import etree
import logging
log = logging.getLogger(__name__)


# Argument definition
Parameter = namedtuple('Parameter', 'type name')

# Optional argument


class OptArg(Node):
    '''
    Latex optional argument.
    This is identical to the Group class except that chars() outputs [ and ] instead of { and }.
    It could probably be subclassed from NodeList instead of Node.
    TODO: read verbatim then split into args and kwargs (see misc.py)
    '''

    def __init__(self):
        Node.__init__(self)

    # def __init__(self, args, kwargs=None):
    #     Node.__init__(self)
    #     self.args = args # list
    #     self.kwargs = kwargs # dict

    def chars(self, **kwargs):
        s = []
        for child in self.children:
            s.append(child.chars())
        return '[{}]'.format(''.join(s))

    def __repr__(self):
        # return '{}:{}:{}()'.format(self.family, self.genus, self.species)
        return '{}:{}()'.format(self.genus, self.species)


class ArgTable(OrderedDict):
    '''
    An ordered dictionary of arguments. 
    We need to remember the order in which arguments are parsed, so that they
    can be printed in the correct order when recovering the source. 
        - delimited arguments are Group objects
        - undelimited arguments are Node objects (Command, Text ...)
    TODO: basic type checking
        - allowed types are Group, Command, OptArg, Text
    '''
    counter = 0  # for debugging

    def __init__(self, keys=None):
        self.number = ArgTable.counter
        ArgTable.counter += 1
        OrderedDict.__init__(self)
        if keys:  # list of argument names
            for key in keys:
                OrderedDict.__setitem__(self, key, None)

    def insert(self, arg):
        # if not isinstance(arg, Node):
        # Exception('ArgTable can only contain Node objects')
        self[arg.species] = arg

    def chars(self, **kwargs):
        s = []
        for arg in self.values():   # ignore keys when writing back to Latex format
            if not arg:             # ignore unused optional arguments
                continue
            if 'insert_strict_braces' in kwargs and kwargs['insert_strict_braces'] and not arg.species == 'Group':
                s.append('{' + arg.chars() + '}')
            else:
                s.append(arg.chars())
        return ''.join(s)

    def pretty_print(self, depth=0, indent_str='----'):
        ''' print opt args only when set '''
        s = []
        for name, arg in self.items():
            if arg:
                s.append(indent_str*(depth) + 'arg:' + name)  # arg name
                s.append(arg.pretty_print(depth=depth+1))
        return '\n'.join(s)

    def xml(self):
        ''' print opt args only when set '''
        args_elt = etree.Element('args')
        for name, arg in self.items():
            if arg:
                elt = etree.Element(name)
                elt.append(arg.xml())
                args_elt.append(elt)
        return args_elt


def parse_definition(s):
    '''
    Parse control_char, command or environment definition
    Returns cmd_name and params
    For example: 'chapter[*][short-title]{title}',
        cmd_name = `chapter`
        params = [Parameter('s', 'starred'), Parameter('o', 'short_title'), Parameter('m', 'title')] 
    For example: 'newcommand{cmd}[args][opt]{def}',
        cmd_name = newcommand
        params = [Parameter('m', 'cmd'), Parameter('o', 'args'), Parameter('o', 'opt'), Parameter('m', 'def')]
    '''
    atoms = list(s)
    atoms.reverse()
    cmd_name = ''
    params = []

    # read control char symbol ...
    if atoms and not atoms[-1].isalnum():
        cmd_name = atoms.pop()

    # ... or read command/env name
    else:
        while atoms and (atoms[-1].isalpha() or atoms[-1] == '*'):
            cmd_name += atoms.pop()

    # scan for arguments
    while atoms:

        # scan for bracket type
        if atoms and atoms[-1] == '{':
            param_type = 'm'  # mandatory
        elif atoms and atoms[-1] == '[':
            param_type = 'o'  # optional
        else:
            return None

        # pop left bracket
        atoms.pop()

        # read arg name
        param_name = ''
        while atoms and not atoms[-1] in ['}', ']']:
            param_name += atoms.pop()

        # pop closing bracket
        if atoms and ((param_type == 'm' and not atoms[-1] == '}') or (param_type == 'o' and not atoms[-1] == ']')):
            return None
        atoms.pop()

        # check for starred (specified as 'chapter[*]
        if param_name == '*':
            params.append(Parameter(type='s', name='starred'))
        else:
            params.append(Parameter(type=param_type, name=param_name))

    return cmd_name, params


def main():
    test_strings = [
        r'addtocounter{counter}{value}',
        r'chapter[*][short-title]{title}',
        r'newenvironment{nam}[args]{begdef}{enddef}',
        r'newtheorem{name}[numbered_like]{caption}[numbered_within]',
    ]
    for s in test_strings:
        name, params = parse_definition(s)
        print('{:20}{}'.format(name, params))


if __name__ == '__main__':
    main()
