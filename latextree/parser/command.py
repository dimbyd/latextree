# command.py
# pylint: disable=no-member
r'''
Class definitions for commands (catcode 0).

The abstract class `Command` is subclassed into:
    - `Command'           \textbf{xx}   # cmd applied to its arguments 
    - `Declaration'       \small        # cmd changes global state variable
    - `Environment'       \begin{itemize} ... \end{itemize}
                          \itemize ... \enditemize
    - `Macro'             \newcommand{\hello}[1]{Hi #1}
    - `UserDefined'       \hello{Bob}

Declarations:
    - switch mode:     \small, \bf, etc.        Are these "block declarations"?
    - set variable:    \setlegnth{\parindent}{0ex}

Some declarations only apply within the current `scope'.

Commands have the following attributes
    - args          All cmd objects are initialized with an empty ArgsTable()
                    This is to avoid having to use `hasattr' all the time

    - starred       Boolean - numbers are not set if True.

    - noexpand      Boolean - if True then node.chars() ignores children
                        (1) custom commands eg \hello{Bob}
                        (2) numeric labels declared by e.g. \thesection
                    By default all arguments and children are expanded.

    - post_space    Records any space following the cmd, so that the tree 
                    can be inverted correctly (needed for testing).
 
 Label attributes are set during post-processing.
 Numbers are set on-the-fly but this can also be done post-hoc.

Additional attributes:
`symbol'    control characters are represented by classes named 
            according to the Latex \CharacterTable, for example
                \! is encoded as <Exclamation/>
            we set `cmd.symbol='!' to avoid having to consult the table every time.
            see coredefs.py
        
`number'    all `numbered' and `numbered_like' species are initialized
            with `number=0'. When an instance of the command is parsed, 
            its value is set to the current value of appropriate counter
            provided that `starred=False'.


Environments are particular types of command 
    - those with a specific end marker
    - block commands and declarations can have more than one end marker


A command definition has parameters (keys defined in coredefs.py).
A command object has arguments (values provided in the source file).
The arguments (parameter values) passed to an instance of the command
belong to the corresponding node.
    - \setcounter changes a global variable, but it's still encoded in the tree
    - subsequent nodes have a possibly modified number attribute value
Every command instance creates at least one Node in the tree
    - arguments creates sub-trees indexed by name (args)
    - delimited content creates a list of sub-trees (children)

Input commands
    - \input, \include
    - \bibliography
The file name is recorded as input.args['file'] (as defined in coredefs.py)
The contents of the file is parsed into input.children    


Superscript, Subscript and ActiveCharacter 
    These should probably be hived off somewhere else because they 
    are not really commands as such, however they have arguments 
    and post_space so it makes sense to sub-class them from Command 
    to avoid unnecessary work.


Finally note that `Group` is defined as a subclass of `Nodelist`,
    - `Group`             { ... }
because they don't have arguments, numbers, etc.

'''

from lxml import etree
from .node import Node
from .parameter import ArgTable


class Command(Node):
    r'''
    Node to represent Latex commands
    Base class for:
        Environment, Block, Declaration, Command
    
    Attributes attributes:
        1. `starred` (default=`False`)
        2. `noexpand` (default=`False`)
    
    '''
    def __init__(self):
        Node.__init__(self)
        self.args = ArgTable()
        self.starred = False
        self.noexpand = False
        self.post_space = ''


    def __repr__(self):
        if hasattr(self, 'symbol'):
            return '{}:{}({})'.format(self.genus, self.species, self.symbol)
        elif hasattr(self, 'marker'):
            return '{}:{}({})'.format(self.genus, self.species, self.marker.chars())
        elif hasattr(self, 'number'):
            return '{}:{}({})'.format(self.genus, self.species, self.number)
        return '{}:{}'.format(self.genus, self.species)


    def chars(self, **kwargs):
        
        # init sub-string list
        s = ['\\']
        
        # append name
        # check for control characters eg <Exclamation/> or <Dollar/>
        if hasattr(self, 'symbol'):
            s.append(self.symbol)
        else:
            s.append(self.species)
        
        # check whether starred
        if self.starred:
            s.append('*')
        
        # append post space
        s.append(self.post_space)
        
        # recurse into arguments
        if self.args:
            s.append(self.args.chars(**kwargs))
        
        # recurse into children (overridden in Command)
        if not self.noexpand:
            for child in self.children:
                s.append(child.chars(**kwargs))
        
        return ''.join(s)


    def xml(self):
        elt = etree.Element(self.species)
        if hasattr(self, 'symbol'):
            elt.set('symbol', self.symbol)
        if self.starred:
            elt.set('starred', 'True')
        if self.args:
            elt.append(self.args.xml())
        for child in self.children:
            elt.append(child.xml())
        return elt


    def pretty_print(self, depth=0):
        s = []
        indent_str = '----'
        s.append(indent_str*depth + repr(self))
        if self.args: 
            s.append(self.args.pretty_print(depth+1, indent_str=indent_str))
        for child in self.children:
            s.append(child.pretty_print(depth=depth+1))
        return '\n'.join(s)


class Declaration(Command):
    r'''
    A declaration has no arguments but instead changes the context (within scope)
    TODO: but how about \setcounter{chapter}{4}
        - this changes the context too!
    At the moment we are thinking of them as "mode switches" (no arguments)
    '''    
    def __init__(self):
        Command.__init__(self)
    
    # def chars(self, **kwargs):
    #     dec_name = self.species
    #     if self.starred:
    #         dec_name += '*'
    #     s = ['\\', dec_name + self.post_space]
        
    #     return ''.join(s)


class UserDefined(Command):
    r'''
    To represent new commands defined by
        - \def, \newcommand, \newenvironment, etc.
    The expansion is stored in the `children' array of
    the phenotype, so we override `chars()' to exclude them
    This is because `chars' has to recover the original source,
    so we need \hello{bob} and not "Hi Bob".
    
    (1) For example in the preamble:
        \newcommand{\hello}[1]{Hi #1} 
    yields
        Command:Macro:newcommand
    with arguments
        name: 'hello'
        numargs: 1
        def: 'Hi #1'
    
    (2) Then in the document:
        \hello{Bob}
    yields
        Command:UserDefined:hello
    with arguments
        arg1:   Bob

    '''    
    def __init__(self):
        Command.__init__(self)
    
    def chars(self, **kwargs):
        s = ['\\' + self.species]
        if self.starred:
            s.append('*')
        s.append(self.post_space)
        if self.args:
            s.append(self.args.chars(**kwargs))
        return ''.join(s)
    
  
class Macro(Command):
    r'''
    To represent commands such as \def, \newcommand, ...
    '''    
    def __init__(self):
        Command.__init__(self)
    
    def chars(self, **kwargs):
        s = ['\\' + self.species]
        if self.starred:
            s.append('*')
        s.append(self.post_space)
        if self.args:
            s.append(self.args.chars(**kwargs))
        return ''.join(s)
    

class Environment(Command):
    r'''
    To represent environments.
    The `args` field contains arguments to the environment (if any)
            - e.g. \begin{tabular}{ccc} ... \end{tabular}
    The `children` field contains the contents of the environment
    Environments can inline or display. 
    For example \begin{math} ... \end{math} is a synonym for $ ... $ 
    '''
    def __init__(self):
        Command.__init__(self)
        self.tex_style = False
        self.pre_space = ''
        self.pre_children = []  # begdef for user-defined environments
        self.post_children = [] # enddef for user_defined environments


    def chars(self, **kwargs):

        # set name
        env_name = self.species
        if self.starred:
            env_name += '*'

        # top-and-tail
        if self.tex_style:
            pre = '\\{}{}'.format(env_name, self.pre_space)
            post = '\\end{}{}'.format(env_name, self.post_space)
        else:
            pre = '\\begin{}{{{}}}'.format(self.pre_space, env_name)
            post = '\\end{}{{{}}}'.format(self.post_space, env_name)

        s = []
        # recurse into arguments
        if self.args:
            s.append(self.args.chars(**kwargs))
        
        # recurse into children (but not pre_children nor post_children)
        for child in self.children:
            s.append(child.chars(**kwargs))

        return pre + ''.join(s) + post


class Numeral(Command):
    '''
    For \arabic{chapter} etc
    The numeral itself (e.g. 'A.3') is recored as 
        self.children = [Text('A.3')]
    with 
        self.noexpand = True
    so that these are ignored by node.chars()

    '''
    def __init__(self):
        Command.__init__(self)
        self.noexpand = True
   
   
class Input(Command):
    r'''
    Class to represent \input, \include and \bibliography commands.
    These are pre-processor directives.
    We override `chars()' so suppress the children (which contain the expansion)
    '''        
    def __init__(self):
        Command.__init__(self)
        
    def chars(self, **kwargs):
        s = ['\\' + self.species]
        if self.starred:
            s.append('*')
        s.append(self.post_space)
        if self.args:
            s.append(self.args.chars(**kwargs))
        return ''.join(s)


class Superscript(Command):
    r'''
    Catcode 7 Superscript
    Arguments can be delimited or undelimited
        ^{...}      Group node (list)
        ^\infty     Command node (single)
        ^1          Text node (single)
    '''
    def __init__(self):
        Command.__init__(self)

    def chars(self, **kwargs):
        s = ['^', self.post_space]
        s += self.args.chars(**kwargs)
        return ''.join(s)


class Subscript(Command):
    r'''
    Catcode 8 Subscript
    Arguments can be delimited or undelimited
        _{...}      Group node (list)
        _\epsilon   Command node (single) 
        _0          Text node (single)
    '''
    def __init__(self):
        Command.__init__(self)

    def chars(self, **kwargs):
        s = ['_', self.post_space]
        s += self.args.chars(**kwargs)
        return ''.join(s)


class ActiveCharacter(Command):
    r'''
    Catcode 13. Active characters - typically only tilde (~)
    Active characters are "commands" that do not have a \ prefix.
    These include _ and ^ in mathmode ...
    '''
    def __init__(self, char):
        Command.__init__(self)
        if not len(char) == 1:
            raise Exception('Invalid input: single character required (not {})'.format(char))
        elif not ord(char) < 128:
            raise Exception('Invalid input: ascii character required (not {}).'.format(char))
        elif char.isalnum():
            raise Exception('Invalid input: non-alpha numeric character required (not {}).'.format(char))
        else:
            self.char = char

    def __repr__(self):
        return '{}:{}({})'.format(self.genus, self.species, self.char)

    def chars(self, **kwargs):
        return r'{}'.format(self.char)

    def xml(self):
        elt = etree.Element(self.species)
        if self.args:
            elt.append(self.args.xml())
        return elt

    def pretty_print(self, depth=0):
        s = []
        indent_str = '----'
        s.append(indent_str*depth + repr(self))
        if self.args: 
            s.append(self.args.pretty_print(depth+1, indent_str=indent_str))
        return '\n'.join(s)



# test
def test_command():

    o = Command()
    o.__setattr__('symbol', '$')
    print(o)
    print(o.species)
    print(o.genus)

    print(Command)

if __name__ == '__main__':
    test_command()

    
