# parser.py
r'''
--------------------
Entry point for parsing latex strings.
File i/o is carried out by the LatexTree class
The parser returns the root of the tree.

kwargs for parsing
    bibtex = True
        - default expands \bibliography{refs.bib} commands
        - bibtex=False scans for \begin{thebibliography}{} \bibitem{cite_key} ...

kwargs for output
    tex_delimiters = True
        - output $ ... $ instead of \( ... \) 
        - output $$ ... $$ instead of \[ ... \]
    non_breaking_spaces = False
        - replace spaces by tildes
        - makes output robust to rewriters
    strict_braces = False
        - replace e.g. \int_0^1 by \int_{0}^{1}
        - makes output robust to rewriters

For any command, TeX expects the specific number of mandatory arguments.
LaTeX implements optional arguments by
    1. a peek() to see whether the next character is a '[' or '*'
    2. calling a TeX command to deal with it.
        TODO: we need to read them verbabim and parse kwargs etc.

For TeX there are only two types of argument
    1. undelimited  e.g. \def\test#1#2#3{do something with #1 #2 #3}
    2. delimited    e.g. \def{\hello}{Hi}

Undelimited arguments: \def\test#1{\def\result{#1}}
If the first token after \test is not a character with catcode 1 then 
this next token simply becomes the argument, otherwise it scans further 
and looks only at catcodes until it sees an equal number of
tokens with catcode 1 and 2, in other words a balanced set of brace groups.
It then strips off the outer set of tokens and the remaining material 
becomes the argument. The braces surrounding an argument will not become 
part of the argument, however any further braces inside will remain.

Trailing Whitespace
Latex ignores some whitespace e.g. between a control sequences and its first argument
    e.g. \textbf    {some text} is fine!
tokens.tokenize records ignored whitespace as (16, '  ') tokens
ControlSeq objects record this in the attribure `post_space`

A space might be necessary 
    - to terminate a command: e.g. \alpha e^x
    - to define an argument e.g. \textbf A

TeX rule: "if the next token is not '{' then the next token becomes the argument, ignoring trailing space"

\LaTeX3 and \LaTeX 3 produce identical output 
      - because the control sequence \LaTeX expects no arguments

This is also true also in mathmode: $\alpha3$ and $\alpha 3$ produce identical output
    - the "ignored" space is recorded in (e.g.) alpha.post_space

This is NOT true for control characters that expect no arguments
    i.e. in these cases a space following a control character is printable
e.g. \$3 prints '$3' but \$ 3 prints '$ 3'

These also record the space in (e.g.) Dollar().post_space

    \newcommand{\hello}[1]{Hi #1} 

1. Parse preamble: record commands (don't expand the command definition):
The 'hello' species is added to 
    (a) registry.species    - map species name to new class (subclass of Command:Command)
    (b) registry.params    - map species name to argument definitions (parameters?)
    (c) registry.custom   - map species name to latex definition (expanded in-situ)

2. Parse document: expand command and the argument values 

    \hello{Bob} -> (0,'hello'), (3,'{'), (11,'B'), (11,'o'), (11,'b'),(4,'}')})
    token = Token(0,'hello')
    \hello{Bob} -> Command:Command:hello with hello.args['arg1'] = Group(Text(Bob))

The expanded macro (with arguments substituted for the parameters) is recorded
as children of a Command:Macro:hello object.

For example a `hello' object is created when arguments are provided (in the body)
and the macro is expanded. The resulting nodes ae recorded as the children 
of the `hello'` object. 

Some examples:
`\include{intro.tex}'
    Command:Input:include.args['file'] = Group([Text('intro.tex')])

`\includegraphics{mypic.png}'
    Command:Input:includegraphics.args['file'] = Group([Text('mypic.png')])

`\label{sec:intro}'
    Command:Anchor:label.args['key'] = Group([Text('sec:intro')])

`\url{http://example.com}'
    Command:Link:url.args['url'] = Group([Text('http://example.com')])

`\href{http://example.com}{click here}'
    Command:Link:url.args['url'] = Group([Text('http://example.com')])
    Command:Link:url.args['text'] = Group([Text('click here'm')])

'''

import os
import json

# logging
import logging
log = logging.getLogger(__name__)
logging.basicConfig(
    filename = 'parser.log', 
    format = '%(levelname)8s:%(name)8s:%(funcName)20s:%(lineno)4s %(message)s',
)
# log.setLevel(logging.WARNING)
# log.setLevel(logging.DEBUG)
log.setLevel(logging.INFO)

from .tokens import Token, TokenStream, EndToken
from .node import Node, NodeList
from .group import Group
from .command import Command, Declaration, Environment
from .command import Input, Macro, UserDefined
from .command import Superscript, Subscript, ActiveCharacter
from .parameter import Parameter, ArgTable, OptArg
from .maths import Inline, Display
from .tabular import Row, Cell
from .content import Text, Number
from .vertical import ParagraphBreak
from .comment import Comment
from .registry import Registry, ClassFactory

from .misc import write_roman
# spec
from .coredefs import defs

# output
from lxml import etree
from termcolor import colored


class Parser():
    '''
    Latex parser class. Converts Latex source into a tree of Node objects
    The main `parse` function returns a Node object of type Root
    The `Parser` class only deals with string input. 
        - the `LatexTree` class handles file i/o.
    '''

    def __init__(self):

        # source root (set in `parse_file')
        self.LATEX_ROOT = None

        # init registry
        self.registry = Registry(defs)

        # init counters
        self.counters = dict.fromkeys(self.registry.numbered.keys(), 0)


    def read_defs_file(self, defs_file):
        '''
        Parse definitions in JSON format.
        '''
        try:
            with open(defs_file, 'r') as input_file:
                log.info('Reading definitions from {}'.format(defs_file))           
                more_defs = json.load(input_file)
                self.registry.update_defs(more_defs)
        
        except FileNotFoundError as e:
            raise Exception('File {} not found'.format(e.filename))
        
        # reset counters table (all defs should be loaded before parsing begins)
        self.counters = dict.fromkeys(self.registry.numbered.keys(), 0)



    def tokenize_file(self, tex_file):
        '''
        Read and tokenize a tex file
        '''
        try:
            with open(tex_file) as f:
                log.info('Reading from .{}'.format(tex_file))
                return TokenStream(f.read())

        except FileNotFoundError as e:
            raise Exception('File {} not found'.format(e.filename))


    def parse_file(self, tex_main, LATEX_ROOT=None):
        r'''
        Any source containing \input or \include cmds
        must be parsed from .a main source file to set
        LATEX_ROOT and thus find the input files.
        '''
        if not LATEX_ROOT:
            self.LATEX_ROOT = os.path.dirname(os.path.abspath(tex_main))
        else:
            self.LATEX_ROOT = LATEX_ROOT

        try:
            with open(tex_main) as f:
                log.info('Reading from .{}'.format(tex_main))
                tokens = TokenStream(f.read())
                siblings =  self.parse_tokens(tokens)
                root = ClassFactory('Root', [], BaseClass=Node)() # instantiate!
                root.append_children(siblings)
                return(root)

        except FileNotFoundError as e:
            raise Exception('File {} not found'.format(e.filename))


    def parse(self, s, **kwargs):
        r'''
        Parse a latex string. This should be the only entry point!
        Wrapper for the recursive function parse_tokens.
        File i/o is performed in the main LatexTree class.
        '''
        log.info('===========================================') 
        log.info('START PARSE')
        log.info('input: {}'.format(s))
        
        # parse
        tokens = TokenStream(s)
        log.info('tokens: {}'.format(tokens))
        siblings =  self.parse_tokens(tokens, **kwargs)
        
        # create root node
        root = ClassFactory('Root', [], BaseClass=Node)() # instantiate!
        root.append_children(siblings)

        # post processing
        # set labels (post-hoc because it relies on parents)
        # root.set_labels() 

        log.info('END PARSE') 
        log.info('===========================================') 
        
        return root


    def parse_tokens(self, tokens, stop_tokens=[], replace_stop_token=False, **kwargs):
        r'''
        The main recursive function.
        Parses the token stream until the first stop token is encountered.
        Returns a :py:class:`NodeList` object. 
        '''      

        # init return list
        siblings = NodeList()
        
        # check for empty stream or EndToken
        if not tokens or tokens.peek() == EndToken:
            return siblings  # empty

        # allow single stop tokens to be specified (default is list)
        if isinstance(stop_tokens, Token):
            stop_tokens = [stop_tokens]

        # init output buffer for printable characters (catcodes 10,11,12)
        output = []

        #------------------------------
        # start popping tokens
        while tokens:

             # pop next
            t = tokens.pop()
            log.debug('PARSE_TOKENS')
            log.debug('Curr token:  {}'.format(t))
            log.debug('Stop tokens: {}'.format(stop_tokens))
            
            # --------------------
            # check for stop token
            if t in stop_tokens:

                log.debug('Stop token found: {}'.format(t))
                log.debug('replace_stop_token = {}'.format(replace_stop_token))

                # return stop token to stream if required
                if replace_stop_token:
                    tokens.push(t)

                # append trailing chars from .output buffer (if any) and exit
                if output:
                    s = ''.join(output)
                    siblings.append(Text(s))

                # return nodes 
                log.debug('End recursion and return: {}'.format(siblings))
                return siblings
                
            
            # --------------------
            # check for noexpand (repeat verbatim until next stop token)
            if 'noexpand' in kwargs and kwargs['noexpand']:
                if t.catcode == 0:
                    output.append('\\')
                output.append(t.value)
                # more = self.parse_tokens(tokens, stop_tokens=stop_tokens, noexpand=True)
                # output.append(more.chars())
                continue

            # --------------------
            # check for prinable character (catcodes 10, 11, 12)
            # these are accumulated in the output buffer
            # and dumped into Text() nodes when a non-printable
            # character is encountered.
            if t.catcode in [10, 11, 12]:
                
                # append to output buffer
                log.debug("'{}' added to output buffer".format(t.value))
                output.append(t.value)
                continue

            # if not a printable character, print buffer contents 
            # into a Text node, then branch on remaining catcodes
            else:
                if output:
                    log.debug("'{}' appended as Text node".format(''.join(output)))
                    siblings.append(Text(''.join(output)))
                    output = []  # empty ready for the next time

            
            # --------------------
            # Command (0, cmd_name)
            if t.catcode == 0:
                log.info('Command token is: {}'.format(t))
                    
                # init node 
                node = None

                # push token back onto stream before invoking
                # parse_environment or parse_command. This avoids
                # having to pass the `node' object as an
                # argument to these functions
                tokens.push(t)

                # environment
                if t.value == 'begin':
                    node = self.parse_environment(tokens)
                # tex-style environment
                elif self.registry.is_environment(t.value):
                    node = self.parse_environment(tokens, tex_style=True)
                # command 
                else:
                    node = self.parse_command(tokens)
                
                # append to return list
                if node:
                    siblings.append(node)

            # --------------------
            # Begin Group (1, '{')
            elif (t.catcode == 1):
                
                # replace token and call parse_group
                tokens.push(t)
                node = self.parse_group(tokens)
                
                # append to output
                siblings.append(node)

            # --------------------
            # End Group (2, '}') 
            elif t.catcode == 2:
                
                # we should never reach here ... 
                assert(False)
                
            # --------------------
            # Mathmode (3, '$')
            elif t.catcode == 3:
                
                node = None

                # display ($$)
                if tokens and tokens.peek() == Token(3,'$'):
                    tokens.pop()
                    node = Display()
                    kids = self.parse_tokens(tokens, Token(3,'$'))
                    if tokens and tokens.peek() == Token(3,'$'):
                        tokens.pop()
                        node.append_children(kids)
                    else:
                        raise Exception('double dollars don\'t match')
                
                # inline ($)
                else:
                    node = Inline()
                    kids = self.parse_tokens(tokens, Token(3,'$'))
                    node.append_children(kids)

                # append to output
                if node:
                    siblings.append(node)

            # --------------------
            # Alignment (4, '&')
            # These are dealt with in parse_tabular
            elif t.catcode == 4:
                siblings.append(Text(text='&'))
            
            # --------------------
            # Alignment (5, '\n')
            elif t.catcode == 5: 

                    # scan for a paragraph break (blank line)
                    spaces = []
                    while tokens and tokens.peek().catcode == 10:
                        spaces.append(tokens.pop().value)
                    
                    # check whether first non-space is a second newline
                    if tokens and tokens.peek().catcode == 5:
                        siblings.append(Text(''.join(output))) # append current output as Text node
                        output = []
                        pb_node = ParagraphBreak(''.join(spaces))
                        siblings.append(pb_node)
                        tokens.pop()    # pop the newline
                    
                    # no blank line, so append the newline and spaces
                    # to the chars output 
                    else:
                        output.append(t.value)
                        output.extend(spaces)
                
            # --------------------
            # Parameter (6, '#') 
            # These are dealt with in parse_macro
            elif t.catcode == 6:
                siblings.append(Text(text='#')) # append to text

            # --------------------
            # Superscript (^)
            elif t.catcode == 7:
                # create node
                node = Superscript()
                # return token and parse argument
                tokens.push(t)
                node.args = self.parse_arguments(tokens)
                # append to output
                siblings.append(node)

            # --------------------
            # Subscript (_)
            elif t.catcode == 8:
                # create node
                node = Subscript()
                # return token and parse argument
                tokens.push(t)
                node.args = self.parse_arguments(tokens)
                # append to output
                siblings.append(node)

            # --------------------
            # Invalid character (null) 
            elif t.catcode == 9:
                # do nothing (continue to next token)
                pass

            # --------------------
            # Active characters - usually only tilde (~)
            elif t.catcode == 13:
                # create ActiveCharactoer object
                ac = ActiveCharacter(t.value)
                # TODO: we need to parse arguments here!!!
                pass
                # append to output
                siblings.append(ac)

            # --------------------
            # Comment (%)
            elif t.catcode == 14:
                # return token and call parse_comment
                tokens.push(t)
                comment_node = self.parse_comment(tokens)
                # append to output
                siblings.append(comment_node)
                
            # --------------------
            # Invalid character
            elif t.catcode == 15:
                log.info('Invalid character: {}'.format(t))
                break

            # --------------------
            # Token not recognised
            # This catches unassigned post_space tokens (16, '   ')
            else:
                raise Exception('Token {} not recognised'.format(t))
        
        # return siblings
        # Note: the end_token cleans up any trailing characters
        log.debug('End parse_tokens with final token: {}'.format(t))
        return siblings


    def parse_group(self, tokens, noexpand=False):
        '''
        Input is a `TokenStream' object. First token must be (1, '{')
        Tokens are parsed until the corresponding (2, '}') is encountered
        Returns a `Group' object
        '''
        t = tokens.pop()
        if not t == Token(1,'{'):
            raise Exception('Error: parse_group: first token must be (1,{)')
        
        node = Group()
        # expand 
        if not noexpand:
            sibs = self.parse_tokens(tokens, Token(2, '}'))
        
        # noexpand (used in macros)
        # any stack symbols would do the trick
        else:
            s = ''
            stack = ['{']
            while stack:
                if tokens.peek() == Token(1,'{'):
                    stack.append('{')
                elif tokens.peek() == Token(2,'}'):
                    stack.pop()
                elif tokens.peek == Token(0,'begin'):
                    stack.append('begin')
                elif tokens.peek == Token(0,'end'):
                    stack.pop()
                if tokens.peek().catcode == 0:
                    s += '\\'
                s += tokens.pop().value
            s = s[:-1] # discard final '}'
            sibs = [Text(s)]

        node.append_children(sibs)
        return node

    
    def parse_command(self, tokens, **kwargs):
        r'''
        Parse command.
        The first token must be the command name e.g. (0,'item')
        This does not necessarily only produce Command objects
        For example, \[...\] creates a Display object 
        '''
                    
        # pop command token 
        t = tokens.pop()
        if not t.catcode == 0:
            raise Exception("Command token expected (catcode 0)")

        # check for starred
        starred = False
        if tokens.peek() == Token(12,'*'):
            tokens.pop()
            starred = True

        # mathmode 
        #   - Inline is a subclass of Group
        #   - Display is a subclass of Environment
        if t in [Token(0, '('), Token(0, '[')]:

            # display or inline            
            if t == Token(0,'('):
                node = Inline(delimiter='latex')
                stop_token = Token(0, ')')
            else:
                node = Display(delimiter='latex')
                stop_token = Token(0, ']')

            # parse tokens and deal with spaces
            if tokens and tokens.peek().catcode == 16:
                node.pre_space = tokens.pop().value
            sibs = self.parse_tokens(tokens, stop_token)
            node.append_children(sibs)
            if tokens and tokens.peek().catcode == 16:
                node.post_space = tokens.pop().value
            
            return node
        
        # create object        
        cmd = self.registry.create_phenotype(t.value, base_class=Command)
        cmd.starred = starred

        if tokens and tokens.peek().catcode == 16:
            cmd.post_space = tokens.pop().value
        
        # replace original token (which carries the command name)
        # then parse arguments 
        tokens.push(t)
        if cmd.genus == 'Macro':
            cmd.args = self.parse_arguments(tokens, noexpand=True)
        else:
            cmd.args = self.parse_arguments(tokens)
        
        # set parent node of arguments (messy - it would be better to pass cmd to parse_arguments)
        for arg in filter(None, cmd.args.values()):
            arg.parent = cmd
        
        # set number (done before recursion but after parse_arguments)
        if not cmd.starred:
            self.set_number(cmd)
        
        # --------------------
        # numbers
        #
        # Genus `Numeric' are cmds of the form `\arabic{chapter}' or `\alph{section}' 
        # All species of genus `Numeric' have a named
        # argument called `counter'. We want to set the
        # content to be a Number() object - these store
        # integer values (Text objects store strings).
        # We attach the number as a child of the `Numeric' object
        # not as an attribute: the only named parameter of
        # a `numeric' object is `counter' (which specifies which
        # counter value to record). This applies to the species
        # but not specifically to this phenotype.

        if cmd.genus == 'Numeral' and 'counter' in cmd.args:
            cmd.noexpand = True
            counter_name = ''.join([x.chars() for x in cmd.args['counter'].children])
            if counter_name in self.counters:
                cmd.value = int(self.counters[counter_name])

        # Genus `NumericLabel' represents cmd of the form
        #   '\thechapter', `\thesection', ...
        # which are macros defined by e.g
        #   \renewcommand{\thesection}{\arabic{chapter}.\alph{section}}
        # We may want to pass these along to the writer functions
        #
        # This is an example of on-the-fly expansion!!

        if cmd.species[:3] == 'the' and cmd.species[3:] in self.counters:
            counter_name = cmd.species[3:]
            tex_str = self.registry.marker_formats[counter_name]
            new_tokens = TokenStream(tex_str)
            sibs = self.parse_tokens(new_tokens)
            cmd.noexpand = True
            cmd.append_children(sibs)

        # --------------------
        # block commands (non-leaf)
        # The approach here is ...
        #    "parse tokens till next stop_token then append as children"
        #
        # Different species have different stop tokens
        #   
        #   species         stop_tokens
        #   -----           -----------
        #   section         (0,section), (0,chapter), (0,document)
        #   item            (0,item), (0,end), (0,enditemize), ...
        #   bf              (0,it), (0,tt), (0,sc), ...

        if cmd.species in self.registry.block_commands:
            # --------------------
            log.info('block_command: {}'.format(cmd))
            # default stop tokens:
            #   - same token e.g. (0, 'item') or (0, 'section), and 
            #   - end token (0, 'end') (end-of-list for items, end-of-document for sections)
            stop_tokens = [t, Token(0,'end')]  

            # additional stop tokens (from registry.block_commands):
            #   - (0, 'chapter') for (0, 'section')
            #   - (0, 'itemize') for (0, 'item')
            stop_tokens += [Token(0,s) for s in self.registry.block_commands[cmd.species]] 

            # extra stop tokens to catch tex-style environments
            #   - e.g. (0, 'enddocument'), or (0, 'enditemize')
            # TODO: Are these now obsolete because tex-style 
            # environments are caught in `parse_tokens'?
            stop_tokens += [Token(0,'end'+s) for s in self.registry.block_commands[cmd.species]] 

            sibs = self.parse_tokens(tokens, stop_tokens, replace_stop_token=True)
            cmd.append_children(sibs) 
        
        #--------------------
        # declarations
        elif cmd.species in self.registry.block_declarations:
            log.info('block declaration: {}'.format(cmd.species))
            stop_tokens = [Token(0,'end'), Token(2,'}'), Token(12,']'), Token(0,'item'),]
            stop_tokens += self.registry.block_declarations[cmd.species]
            sibs = self.parse_tokens(tokens, stop_tokens, replace_stop_token=True)
            cmd.append_children(sibs)
  
        #--------------------
        # macros (e.g. \def, \newcommand)
        # arguments have already been parsed into the `args' attribute
        # We call `parse_macro` which updates the registry.custom table
        # so that the new commands or environments defined in the preamble
        # can be parsed correctly when they appear in the main body.

        elif cmd.genus == 'Macro':

            log.info('Macro command: {}'.format(cmd.species))
            self.parse_macro(cmd, tokens, **kwargs)
        
        # --------------------
        # user-defined command (recorded in registry.custom table)
        # an example of on-the-fly tokenization (from .snippets)
        
        elif cmd.species in self.registry.custom:

            log.info('User-defined command: {}'.format(cmd.species))
            print('User-defined command: {}'.format(cmd.species))

            # retrieve and expand command definition
            tex_str = self.registry.custom[cmd.species]
            exp_str = self.expand_custom_def(tex_str, cmd.args.values())

            # tokenize (the end_token is needed to stop the recursion in the right place)
            new_tokens = TokenStream(exp_str)
            tokens.extend(new_tokens)

            # parse tokens into children
            sibs = self.parse_tokens(tokens)
            cmd.append_children(sibs)

        # --------------------
        # input commands (input, include, bibliography)
        # 
        elif cmd.genus == 'Input':
            
            log.info('Input command: {}'.format(cmd.species))

            # set noexpand flag (chars doesn't print children)
            # the genus class 'Input' is automatically created
            # from .coredefs.py which is not the same class as 
            # the Input class defined in command.py (which is
            # redundant it seems)
            cmd.noexpand = True

            # read and parse
            if self.LATEX_ROOT:
                filename = cmd.args['file'].chars(nobrackets=True)
                if cmd.species in ['input','include']:
                    if not filename[-4:] == '.tex':
                        filename += '.tex'
                filename = os.path.join(self.LATEX_ROOT, filename)
                newtoks = self.tokenize_file(filename) # inc end_token
                sibs = self.parse_tokens(newtoks)
                cmd.append_children(sibs)

        # --------------------
        # return cmd object
        return cmd


    def parse_environment(self, tokens, tex_style=False, **kwargs):
        '''
        Parse environment. The first token must be (0,'begin').
        Starred environments 
            - \begin{figure*} dealt with in `parse_arguments'
            - end{figure*} dealt with here (popped if present)
        '''
        env_name = ''
        pre_space = ''
        post_space = ''
        stop_token = Token(0,'end') # overwritten for tex-style
        starred = False

        # tex environments
        if tex_style:
            env_name = tokens.pop().value
            if tokens.peek() == Token(12, '*'):
                tokens.pop()
                starred = True
            stop_token = Token(0, 'end'+env_name)
            # record trailing whitespace (after \itemize) if any
            if tokens.peek().catcode == 16:
                pre_space = tokens.pop().value

        # latex environments
        else:
            # pop first token
            if not tokens.peek().value == 'begin':
                raise Exception("First token must be (0,'begin') not {}".format(tokens.peek()))
            tokens.pop()

            # record trailing whitespace (between \begin and {envname}) if any
            if tokens.peek().catcode == 16:
                pre_space = tokens.pop().value

            # parse environment name
            if not tokens.peek().catcode == 1:
                raise Exception("Left brace '{{' expected.")
            tokens.pop()                        # pop '{'
            while tokens.peek().catcode == 11:  # pop name
                env_name += tokens.pop().value
            if tokens.peek() == Token(12, '*'):
                tokens.pop()
                starred = True
            if not tokens.peek().catcode == 2:
                raise Exception("Right brace '}}' expected.")
            tokens.pop()                        # pop '}'

        # create environment object
        env = self.registry.create_phenotype(env_name, base_class=Environment)
        env.starred = starred
        env.pre_space = pre_space
        if tex_style:
            env.tex_style = True
        
        # push dummy token (0,'env_name') to stream and call parse_arguments
        tokens.push(Token(0,env_name))
        env.args = self.parse_arguments(tokens, parse_undelimited=False)

        # set number
        if not env.starred:
            self.set_number(env)

        #--------------------
        # parse contents - deal with special cases first
        # arguments have already been parsed into env.args

        # lists
        if env.genus == 'List':
            if env.species == 'itemize':
                self.registry.is_enum = False
                sibs = self.parse_tokens(tokens, stop_token)
            else:
                self.registry.is_enum = True
                self.registry.enum_depth += 1
                # if self.registry.enum_depth == 4:
                #     self.counters['enumiv'] += 1
                # elif self.registry.enum_depth == 3:
                #     self.counters['enumiii'] += 1
                # if self.registry.enum_depth == 2:
                #     self.counters['enumii'] +=1
                # if self.registry.enum_depth == 1:
                #     self.counters['enumi'] += 1
                sibs = self.parse_tokens(tokens, stop_token)
                self.registry.enum_depth -= 1
                if self.registry.enum_depth < 4:
                    self.counters['enumiv'] = 0
                if self.registry.enum_depth < 3:
                    self.counters['enumiii'] = 0
                if self.registry.enum_depth < 2:
                    self.counters['enumii'] = 0
                if self.registry.enum_depth < 1:
                    self.counters['enumi'] = 0


        # tabular
        elif env.species == 'tabular':
            log.info('tabular.args is {}'.format(env.args))
            colspec = ''.join([x.chars() for x in env.args['cols'].children])
            sibs = self.parse_tabular(colspec, tokens, **kwargs)
            
            
        # verbatim
        elif env.genus == 'Verbatim':
            sibs = self.parse_tokens(tokens, stop_token, noexpand=True)

        # user-defined
        elif env.species in self.registry.custom:
            
            log.info('User-defined environment: {}'.format(env.species))
            # extract source from registry.custom
            tex_str_pre, tex_str_post = self.registry.custom[env.species]  
            
            # substitute argument values for the placeholders (#1, #2, etc.)
            # These are only allowed in the `begdef' argument (tex_str_pre)
            # TODO: this repeats the code for user-defined macros (bad)
            for pos, arg in enumerate(env.args.values()):
                seed = '#' + str(pos+1)
                s = arg.chars()
                if arg.species == 'Group':
                    s = ''.join([x.chars() for x in arg.children])
                tex_str_pre = tex_str_pre.replace(seed, s)
            env.pre_children  = self.parse_tokens(TokenStream(tex_str_pre))
            env.post_children = self.parse_tokens(TokenStream(tex_str_post))
            sibs = self.parse_tokens(tokens, stop_token)

        # default (parse contents)
        else:
            sibs = self.parse_tokens(tokens, stop_token)
        
        # recursion terminated by (0,'end') or (0, 'enditemize')
        # now tidy up ...
        if tokens.peek() == Token(12,'*'): # pop star if any
            tokens.pop()
        if tokens and tokens.peek().catcode == 16:
            post_space = tokens.pop().value
        if not tex_style:
            if tokens and not tokens.peek().catcode == 1:
                raise Exception("Left brace '{{' expected.")
            tokens.pop()                        # pop '{'
            while tokens and tokens.peek().catcode == 11:  # pop env name
                tokens.pop()
            if tokens and tokens.peek() == Token(12, '*'): # pop star if any
                tokens.pop()
            if tokens and not tokens.peek().catcode == 2:
                raise Exception("Right brace '}}' expected.")
            tokens.pop()                        # pop '}'
                        
        # attach contents and return environment
        env.append_children(sibs)
        env.post_space = post_space
        return env


    def parse_arguments(self, tokens, noexpand=False, parse_undelimited=True):
        r'''
        Parse the arguments of a command.
        input: `tokens`: a `TokenStream` object (see tokens.py)
            - the first token must be the relevant command 
            - e.g. (0, 'textbf') or (0, 'itemize') 

        output: ArgTable object
        
        We check self.args_table (keyed on species) to see whether 
        there are argument definitions for this type of node. 
        If arguments are defined, the node should already have had 
        the keys of its `ArgTable' attribute initialized to the given 
        argument names during construction. 
        
        Arguments are parsed according to cmd/env definitions.
        Definitions for core Latex types are found in `coredefs.py`
        Additional definitions can be imported from .json files
            - see `examdef.json` in this directory

        Parameter namedtuples have two fields:
            type: 's' for starred (not used), o' for optional, 'm' for mandatory
            name: descriptive name for the argument 
        
        The token immediately after a control sequence 
        can be one of several things: 
            1. a left brace:            call parse_group()
            2. a left bracket:          call parse_optional_argument()
            3. a single character:      \texbf1 or \textbf A
            4. a command:               \textbf\LaTeX
            5. a command symbol:        \textbf\$
        
        as well as the non-TeX 'ignored space' token (16,'   ')

        The command modifier *: e.g. \chapter and \chapter*
            - it's not only to suppress numbers ...
            - \newcommand* creates a command which will not accept carriage returns in any of its arguments.
            - \vspace* adds vertical space that will not disappear at the beginning of a page. 
            - \hspace* adds horizontal space that will not disappear at the beginning of a line.
            - \\* creates a new line which will not cause a page break (so control characters can have starred forms).
            - \tag* (in amsmath) allows you to add markers to replace equation numbers.
        '''

        # init
        argTable = ArgTable()

        # pop command token
        t = tokens.pop()
        # log.info('Command token is {}'.format(t))  

        # init params list
        params = []

        # superscript
        if t.catcode == 7: # ^
            params = [Parameter('m', 'contents')]

        # subscript
        elif t.catcode == 8: # _
            params = [Parameter('m', 'contents')]

        # active char 
        elif t.catcode == 13: # ~
            # TODO: check parameter definitions in registry.active_chars
            return argTable

        # commands 
        elif t.catcode == 0:

            cmd_name = t.value
        
            # bail out if parameters not defined 
            if cmd_name not in self.registry.params or not self.registry.params[cmd_name]:
                log.debug("Parameters not defined for command {}".format(cmd_name))
                return argTable
            
            # retrieve parameter definitions
            params = self.registry.params[cmd_name]
        
        # error
        else:
            raise Exception('Tokens with catcode {} cannot have arguments'.format(t.catcode))

        # iterate over parameters
        for param_type, param_name in params:

            # starred version (always optional)
            # now dealt with in parse_command and parse_environment
            if param_type == 's':
                # if tokens.peek() == Token(12, '*'):
                #     tokens.pop()
                #     starred = True
                pass

            # optional argument 
            elif param_type == 'o': 

                # check for left bracket
                # TODO: parse arg and kwargs and store somewhere
                # Parse kv pairs string
                #
                # 
                log.debug('Parsing optional argument ...')
                if tokens.peek() == Token(12, '['):
                    tokens.pop()
                    arg = OptArg()
                    # s = ''
                    # while not tokens.peek() == Token(12, ']'):
                    #     if tokens.peek().catcode == 0:
                    #         s += '\\'
                    #     s += tokens.pop().value
                    # tokens.pop()
                    # items =  s.split(',')
                    # singles = [item.strip() for item in items if '=' not in item]
                    # doubles = [item.split('=') for item in items if '=' in item]
                    # doubles = dict(doubles)

                    sibs = self.parse_tokens(tokens, Token(12, ']')) # stop token not replaced
                    arg.append_children(sibs)
                    argTable.__setitem__(param_name, arg)

                else:
                    log.debug('Optional argument {} not provided for  {}'.format(param_name, cmd_name))
                    argTable.__setitem__(param_name, None)

            # mandatory argument
            elif param_type == 'm': 

                if tokens.peek().catcode == 16:
                    arg.post_space = tokens.pop().value

                # delimited arguments
                # check for left brace
                if tokens.peek().catcode == 1:
                    arg = self.parse_group(tokens, noexpand=noexpand)  # returns Group object
                    log.debug('arg is {}'.format(arg))
                    log.debug('arg.chars() is {}'.format(arg.chars()))
                    log.debug('next token is {}'.format(tokens.peek()))

                # undelimited arguments (ignored in parse_environment)
                # if no left brace, the next token is the argument
                elif parse_undelimited:
                    atok = tokens.pop()
                    
                    # argument is a command
                    if atok.catcode == 0:
                        # create node
                        arg = self.registry.create_phenotype(atok.value, base_class=Command)
                        if noexpand:
                            arg = Text(arg.chars())

                        if tokens.peek().catcode == 16:
                            arg.post_space = tokens.pop().value
                    
                    # arg is a number or letter
                    elif atok.catcode in [11, 12]:
                        arg = Text(text=atok.value)
                    
                    else:
                        raise Exception('Token {} not valid as command argument'.format(t))
                
                # record argument
                argTable.__setitem__(param_name, arg)

            else:
                raise Exception('Argument type {} not recognised'.format(param_type))

        # end iterate over parameters 
        return argTable


    def parse_macro(self, cmd, tokens, **kwargs):
        '''
        Parse macros (commands that define or redefine other cmds/envs)
            - newcommand, renewcommand, providecommand
            - newenvironment, renewenvironment
            - newtheorem
        
        The arguments have already been parsed in `parse_command'
        with noexpand=True set in 

        which calls this function.

        The keys of the cmd.args table (parameter names) should have 
        already been initialized by the registry class. This means that 
        we don't need to perform checks like
            if 'name' in cmd.args and cmd.args['name']:
        It is enough to write
            if cmd.args['name']:
        ''' 
        #----------
        # 1. \newtheorem
        #   cmd defn is \newtheorem{name}[numbered_like]{caption}[numbered_within]
        #
        # These are environments.
        # Both optional arguments are counter names. 
        #   - at most one of these is allowed in any instance.
        # 
        # if `numbered_like` is missing the species gets its own 
        # counter of the same name.
        # \newtheorem{theo}{Theorem}
        # \newtheorem{lem}[theo]{Lemma} uses the `theo` counter
        # 
        # if `numbered_within` is present then the counter is set 
        # to zero when the `numbered_within` counter is incremented
        #   \newtheorem{theo}{Theorem}[chapter] 
        # resets the `theo' counter to zero at the start of every chapter.
        #
        # TODO: deal with \renewcommand{\thetheo}{\arabic{chapter}.\arabic{theo}}
        #  
        if cmd.species == 'newtheorem':
            
            # extract theorem name (mandatory arg)
            if cmd.args['name']:
                if cmd.args['name'].species == 'Group':
                    new_species_name = ''.join([x.chars() for x in cmd.args['name'].children])
                else:
                    new_species_name = cmd.args['name'].chars()

                # create new class
                base_class = ClassFactory('Theorem', [], BaseClass=Environment)
                new_class = ClassFactory(new_species_name, [], BaseClass=base_class)

                # set argument definition
                params = [Parameter(type='o', name='title')]            

                # update registry
                dict.__setitem__(self.registry.species, new_species_name, new_class)
                dict.__setitem__(self.registry.params, new_species_name, params)
                
            # extract caption (mandatory). Not the same as a figure caption (for example)
            if cmd.args['caption']:
                if cmd.args['caption'].species == 'Group':
                    caption = ''.join([x.chars() for x in cmd.args['caption'].children])
                else:
                    caption = cmd.args['caption'].chars() # TODO: parse for \^ and \it etc. here
                dict.__setitem__(self.registry.theorem_names, new_species_name, caption)

            # check numbered_like argument (optional) 
            if cmd.args['numbered_like']:
                main_counter = cmd.args['numbered_like'].children[0].content
                if main_counter and main_counter in self.counters:
                    dict.__setitem__(self.registry.numbered_like, new_species_name, main_counter)

            # check numbered_within argument (optional - put in reset list of master counter)
            else:
                # init new counter
                dict.__setitem__(self.registry.numbered, new_species_name, [])
                dict.__setitem__(self.counters, new_species_name, 0)

                # if 'numbered_within' in cmd.args:
                if cmd.args['numbered_within']:
                    master_counter = cmd.args['numbered_within'].children[0].content
                    if master_counter and master_counter in self.counters:
                        dict.__setitem__(self.registry.numbered, master_counter, new_species_name)
            

        #----------
        # 2. \newenvironment, \renewenvironment, etc.
        #   cmd defn is \newenvironment{nam}[args]{begdef}{enddef}
        elif cmd.species in ['newenvironment', 'renewenvironment']:

            # extract environment name (mandatory)
            if cmd.args['name']:
                if cmd.args['name'].species == 'Group':
                    new_species_name = ''.join([x.chars() for x in cmd.args['name'].children])
                else:
                    new_species_name = cmd.args['name'].chars()

            # create custom class
            base_class = ClassFactory('UserDefined', [], BaseClass=Environment)
            new_class = ClassFactory(new_species_name, [], BaseClass=base_class)

            # update registry
            dict.__setitem__(self.registry.species, new_species_name, new_class)


            # extract number of arguments (optional)
            params = []
            if 'numargs' in cmd.args and cmd.args['numargs']: # number of arguments
                numargs = int(cmd.args['numargs'].children[0].content)
                if numargs > 0:
                    for pIdx in range(numargs):
                        params.append(Parameter(type='m', name='arg'+str(pIdx+1)))

            # update registry
            dict.__setitem__(self.registry.params, new_species_name, params)

            # update custom table 
            if cmd.args['begdef'] and cmd.args['enddef']:
                tex_str_beg = ''.join([x.chars() for x in cmd.args['begdef'].children])
                tex_str_end = ''.join([x.chars() for x in cmd.args['enddef'].children])
                dict.__setitem__(self.registry.custom, new_species_name, (tex_str_beg, tex_str_end))
 
        #----------
        # \def, \newcommand, \renewcommand or \providecommand
        # species definition is \newcommand{name}[args][opt]{def}
        else:

            # extract macro name
            if cmd.args['name'].species == 'Group':
                new_species_name = ''.join([x.chars() for x in cmd.args['name'].children])
            else:
                new_species_name = cmd.args['name'].chars()

            # strip leading \ 
            if new_species_name[0] == '\\':
                new_species_name = new_species_name[1:]

            # extract parameters
            params = []
            if 'numargs' in cmd.args and cmd.args['numargs']: # number of arguments
                numargs = int(cmd.args['numargs'].children[0].content)
                
                # if `opt` is present, the first argument to the new 
                # command is optional with default value `opt`
                # TODO: how do we trasmit the optional value?
                if 'opt' in cmd.args and cmd.args['opt']:
                    params.append(Parameter(type='o', name='opt'))
                    numargs = numargs - 1
                
                # all remaining arguments (if any) are mandatory
                if numargs > 0:
                    for pIdx in range(numargs):
                        params.append(Parameter(type='m', name='arg'+str(pIdx+1)))

            # create custom class
            new_class = ClassFactory(new_species_name, params, BaseClass=UserDefined)

            # update registry 
            # We still need registry.params because registry.species contains
            # classes initialized with the parameter names but not their types.
            dict.__setitem__(self.registry.species, new_species_name, new_class)
            dict.__setitem__(self.registry.params, new_species_name, params)

            # update custom table 
            # we record the raw tex here: it contains the #1, #2, ... placeholders. 
            # These are parameters. The arguments themselves are given in the document body.
            # 
            # \newcommand\hello[1]{Hello #1}. 
            # By this point we have created 
            #   (1) a new class recorded in registry.species and 
            #   (2) a new list recorded in registry.params (with argument names arg1, arg2 )
            
            # Both are keyed on the species_name 'hello'.
            # Suppose in the document body we write "\hello{world} and \hello{moon}".
            # In the document body we want to read "Hello world and hello moon".
            # So we must expand these "on the fly".
            
            # We will most often want to style the new command directly, e.g.
            #   span.hello { font-style: italic; }
            # so we keep the element `hello' and store the expansion as its chiltren
            # Thus the expanded version appears in the output within the <hello>...</hello>
            # element.
            #
            # For new mathmode commands we can
            #   (1) pass commands on to mathjax verbatim (in a body element with display:none)
            #   (2) expand into standard latex 
            # The second would avoid the need to smuggle the commands into blackboard.

            if cmd.args['def']:
                tex_str = ''.join([x.chars() for x in cmd.args['def'].children])
                dict.__setitem__(self.registry.custom, new_species_name, tex_str)
 

    def parse_tabular(self, colspec, tokens, **kwargs):
        '''
        Parse the contents of a tabular environments
        Arguments are parsed before this function is called and recorded in env.args
        In particular the (mandatory) column specification is contained in env.args['cols']
        First token must be (0, 'tabular') - for consistency it should probably be (0, 'begin')!
        Tokens are parsed until the corresponding (0, 'end') is encountered.

        Vertical lines: e.g. column specification \tabular{|c|c||cc|c|}
            - converted to column_formats = ['Lc', 'Lc', 'LLc', 'c', 'LcR']

        The column format is recored as a cell attribute (for css)
        '''
        column_formats = []
        cformat = ''
        for char in list(colspec):
            if char == '|':
                cformat  += 'L'
            else:
                cformat += char
                column_formats.append(cformat)
                cformat = ''
        if cformat:
            column_formats[-1] += 'R'*len(cformat)

        # initialise node list to contain rows, hlines and initial whitespace
        siblings = NodeList()
        log.info('column_formats are {}'.format(column_formats))
        # start popping tokens
        while tokens:

            # store initial whitespace in a Text() node
            ws = ''
            while tokens.peek().value.isspace():
                ws += tokens.pop().value
            if ws:
                siblings.append(Text(text=ws))
            
            # iterate over row contents
            row = Row()
            column_index = 0
            while tokens.peek() not in [Token(0,'end'), Token(0,'\\')]:
                
                # extract hlines and set row format
                while tokens.peek() == Token(0, 'hline'):
                    name = tokens.pop().value
                    hline = self.registry.create_phenotype(name, base_class=Command)

                    if tokens.peek().catcode in (10, 16):
                        hline.post_space = tokens.pop().value   
                    siblings.append(hline)
                    row.format += 'T'
                
                # create cell (we record the column format in each cell)
                cell = Cell()
                cell.format = column_formats[column_index]
                column_index += 1

                stop_tokens = [Token(0,'end'), Token(4,'&'), Token(0, '\\')]
                kids = self.parse_tokens(tokens, stop_tokens, replace_stop_token=True)
                cell.append_children(kids)
                row.append_child(cell)
                
                # pop (4, '&') token that is replaced by parse_tokens
                # but keep (0, '\\') which serves to break the loop
                if tokens.peek() == Token(4, '&'):
                    tokens.pop()
                # elif tokens.peek() == Token(0, '\\'):
                #     row.append_child(self.registry.create_phenotype('Backslash'))
            
            # append row
            if any([child.children for child in row.children]):
                siblings.append(row)
            else:
                prev_row = next(x for x in reversed(siblings) if x.species == 'Row')
                if prev_row:
                    prev_row.format += 'B'*len(row.format)
            
            #   continue to next row if next token is (0, '\\')
            if tokens.peek() == Token(0, '\\'):
                node = self.parse_command(tokens)
                row.append_child(node)
                continue

            #   break if next token is (0, 'end') or (0, 'endtabular')
            if tokens.peek().value[:3] == 'end':
                tokens.pop()
                break
        
        log.info('table rows are {}'.format(siblings))
        return siblings


    def parse_comment(self, tokens):
        '''
        Parse comment. 
        The opening comment character (%) and the closing newline are discarded.
        We need to convert tokens back to chars
        '''        
        # first token must be comment character
        t = tokens.pop()
        if not t.catcode == 14:
            return None
        
        # convert tokens back to chars, until we encounter a newline token
        chars = ''
        t = tokens.pop() 
        while tokens and not t.catcode == 5:
            if t.catcode == 0:
                chars += '\\{}'.format(t.value)
                if tokens.peek().catcode == 16:
                    post_space = tokens.pop().value
                    if post_space and post_space[-1] == '\n':
                        chars += post_space[:-1]
                        break
                    else:
                        chars += post_space
                if t.value in ['begin', 'end']:
                    chars += '{{{}}}'.format(tokens.pop().value)
            else:
                chars += t.value
            t = tokens.pop()
        
        # return comment node
        return Comment(chars)


    def expand_custom_def(self, tex_str, args):
        '''
        Parse custom command. Returns a list of Node objects.
        `tex_str':
            - a custom command definition in latex source format
            - recorded in registry.custom by some macro command (eg \newcommand)
            - might contain parameter names #1, #2, ...
        arg_list': 
            - list of Node objects passed as arguments.
            - usually cmd.args.values() where cmd is the macro name
        The function expands `tex_str' by replacing the parameter names with 
        these arguments converted back into Latex format. The expanded command
        is then tokenized and parsed in the usual way.

        '''
        # init expanded str
        exp_str = tex_str

        # substitute arguments for parameters
        # check for None type (optional arguments)
        for pos, arg in enumerate(args):
            seed = '#' + str(pos+1)
            s = ''
            if arg:
                if arg.species == 'Group':
                    s = ''.join([x.chars() for x in arg.children])
                else:
                    s = arg.chars()
            exp_str = exp_str.replace(seed, s)    
        
        # return expanded string
        return exp_str


    def set_number(self, node, **kwargs):
        '''
        Set node number then increment/reset counters
        '''
        counter_name = ''

        # check whether node is a numbered or numbered_like species
        if node.species in self.registry.numbered:
            counter_name = node.species
        
        elif node.species in self.registry.numbered_like:
            counter_name = self.registry.numbered_like[node.species]

        elif node.genus == 'Item':
            
            if 'marker' in node.args and node.args['marker']:
                node.marker = node.args['marker'] # fix this
                return
            
            elif self.registry.is_enum == True:
                if self.registry.enum_depth == 1:
                    counter_name = 'enumi'
                elif self.registry.enum_depth == 2:
                    counter_name = 'enumii'
                elif self.registry.enum_depth == 3:
                    counter_name = 'enumiii'
                elif self.registry.enum_depth == 4:
                    counter_name = 'enumiv'
        
        if not counter_name:
            return

        print('set_number: {}'.format(node.species))
        
        # increment counter and set number
        # counters for numbered and numbered_like species should have
        # been created and included in self.counters by this point
        # but we should probably check anyway ...
        self.counters[counter_name] += 1
        node.number = self.counters[counter_name]

        # set marker
        s = '\\arabic{{{}}}'.format(counter_name)
        if counter_name in self.registry.marker_formats:
            s = self.registry.marker_formats[counter_name]
        new_tokens = TokenStream(s)
        num_str = []
        for numeral in self.parse_tokens(new_tokens):
            print(numeral)
            if not numeral.genus == 'Numeral':
                num_str.append(numeral.chars())
                continue
            if numeral.species == 'arabic':
                num_str.append(str(numeral.value))
            elif numeral.species == 'Alph':
                num_str.append(chr(64 + numeral.value))
            elif numeral.species == 'alph':
                num_str.append(chr(96 + numeral.value))
            elif numeral.species == 'Roman':
                num_str.append(write_roman(numeral.value))
            elif numeral.species == 'roman':
                num_str.append(write_roman(numeral.value).lower())
            else:
                print('NUMERAL SPECIES {} NOT RECOGNISED'.format(numeral.species))
        print(num_str)
        node.marker = Text(''.join(num_str))

        # reset other counters
        if node.species in self.registry.numbered:
            for counter_name in self.registry.numbered[node.species]:
                self.counters[counter_name] = 0
        

             
# #==================================================
# # TEST
# def test_parser(verbose=True):

#     # # import test strings from .test_parser module
#     # from .test_parser import test_strings
#     #     strings = test_strings[-2:]

#     test_strings = [
#         # r'\bibliography{test.bib}',
#         # r'\setlength{\parskip}{2ex}',
#         r'Hello world!',
#         r'pre \textbf{Hello} post',
#         r'pre \chapter[intro]{Introduction} post',
#         r'pre pre \$ 3 post post',
#         r'pre $E=mc^2$ post',    
#         r'pre \question[3] post',
#         r'pre \[\sum x_i = 1\] post',
#         r'pre \center inside \endcenter post',
#         r'pre \begin {center}hello\end {center} post',
#         r'pre \begin{tabular}{c} hello \end{tabular} post',
#         r'pre \begin{tabular}{cc}\hline a & b \\[2ex] \hline c & d \\ \hline \end{tabular} post',
#         r'pre \begin   {itemize}\item a \item b\end     {itemize} post',
#         r'pre \itemize   \item    a   \item   b   \enditemize   post',
#         r'pre \chapter*{Intro} post',
#         r'pre \begin{figure*} inside \end{figure*} post',
#         r'pre \newenvironment{myenv}{hello}{bye} \begin{myenv} inside \end{myenv} post',
#         r'\newtheorem{theo}{Theorem}'
#         r'\newtheorem{theo}{Theorem}[section]\begin{theo} inside \end{theo}', 
#         r'\def\strong[1]{\textbf{#1}}',
#         r'\def\logo{\LaTeX}',
#         r'\def\show[1]{\begin{center}#1\end{center}}',
#         r'\def\emph[1]{pre \textbf{#1} \LaTeX post} \emph{hello}',
#         r'\def\doit{pre \begin{center}inside\end{center} post} \doit',
#         r'pre \newcommand{\hello}[1]{Hi #1} \hello{Bob} post',
#         # this is too hard!!
#         # r'''
#         # \def\bit{\itemize}
#         # \def\eit{\enditemize}
#         # \bit \item a \item b \eit
#         # ''',
#         r'\question[10]',
#         r'''
#         pre 
#         \begin{questions} 
#         \question[10] How? 
#         \question[20] Why? 
#         \end{questions} 
#         post
#         ''',
#         r'\graphicspath{{figures/}}',
#         r'pre \input{anotherfile.tex} post',
#         r'pre \includegraphics{mypic.png} post',
#     ]

#     # iterate over test strings
#     for i, s in enumerate(test_strings):
#         print('TEST {}'.format(i))
#         print(s)
#         p = Parser()
#         base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#         defs_file = os.path.join(base_dir,'extensions/examdef.json')
#         print(defs_file)
#         p.read_defs_file(defs_file)
#         # print(p.registry.species.keys())
#         # for name in ['question', 'questions']: #p.registry.species.keys():
#         #     params = ''
#         #     if name in p.registry.params:
#         #         params = p.registry.params[name]
#         #     else:
#         #         print('Name {} not found in registry.params'.format(name))
#         #     print('{:16} {}'.format(name, params))

#         root = p.parse(s)
#         # print('------------------------------')
#         print(root.pretty_print())
#         # print('------------------------------')
#         # print(root.xml_print())
#         # print('------------------------------')
#         # priroot.chars())
#         # print('------------------------------')
#         # print(root.chars(non_breaking_spaces=True))
#         # print('------------------------------')
#         # print(root.chars(insert_strict_braces=True))
#         print('------------------------------')
#         # print(s)
#         print(root.chars())
#         print('------------------------------')
#         if (root.chars() == s):
#             print(colored('True', 'green'))
#         else:
#             print(colored('False', 'red'))
#         print('------------------------------')

        
# if __name__ == '__main__':
#     test_parser()
