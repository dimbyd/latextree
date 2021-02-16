# tokens.py
r'''
Catcodes
0   \                   Escape character 
1   {                   Begin grouping 		
2   }                   End grouping 		
3   $                   Math shift 			
4   &                   Alignment tab 		
5   <return>            End of line 	
6   #                   Parameter 			
7   ^                   Superscript 	
8   _                   Subscript 			
9   <null>              Ignored character
10  <space> and <tab>   Space 				
11  a...z and A...Z     Letter 		
12  everything else     Other 			
13  ~                   Active character
14 %                    Comment character
15 <delete>             Invalid character 
'''

import json

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)

class Token():
    '''
    Token class. Could it be done with a namedtuple?
    '''    
    def __init__(self, catcode, value):
        self.catcode = catcode
        self.value = value
    
    def __repr__(self):
        return '({},{})'.format(self.catcode, repr(self.value))
    
    def __eq__(self, other):
        if isinstance(other, Token):
            return (self.catcode == other.catcode) and (self.value == other.value)
        return False


class EndToken(Token):
    '''
    EndToken class. End marker for TokenStream objects. 
    Not currently used by parser (useful for debugging).
    '''
    def __init__(self):
        Token.__init__(self, 15, '')


class TokenStream(list):

    def __init__(self, s='', end_token=True):

        # tokenize input string
        tokens = []
        if isinstance(s, str):
            tokens  = self.tokenize(s, end_token=end_token)
        
        # init self as list
        list.__init__(self, tokens) 
        log.info('TokenStream created')

    def __eq__(self, other):
        if isinstance(other, TokenStream) and len(self) > 0:
            return all([t1 == t2 for (t1,t2) in zip(self, other)])
        return False

    def pop(self):
        if len(self):
            t = super(TokenStream, self).pop()
            log.debug('{} popped'.format(t))
            return t
        return None

    def push(self, t):
        if isinstance(t, Token):
            log.debug('{} pushed'.format(t))
            self.append(t)
    
    def isempty(self):
        if len(self) > 0:
            return False
        return True 
    
    def peek(self):
        if not self.isempty():
            log.debug('peek: next token is {}'.format(self[-1]))
            return self[-1]
        return None

    def tokenize(self, s, end_token=True):
        '''
        Convert string to tokens.
        '''

        # convert string to a stream of characters
        chars = list(s)
        chars.reverse()

        # initialize token list
        tokens = []
        
        # start popping chars
        while chars:
            c = chars.pop()

            # escape character (extract command)
            if c == '\\':
                
                # check for empty stream
                if not chars:
                    tokens.append(Token(12,c))
                    return tokens
                
                # init cmd
                cmd = chars.pop()
                
                #--------------------
                # scan for cmd word
                if cmd.isalpha():

                    # extract name
                    while chars and chars[-1].isalpha():
                        cmd += chars.pop()

                    log.info('Command word: {}'.format(cmd))
                        
                # record trailing whitespace (space|tab|newline)
                wspace = []
                while chars and chars[-1].isspace():
                    wspace.append(chars.pop())
                wspace = ''.join(wspace)
                
                # push token and whitespace (if any)
                tokens.append(Token(0,cmd))
                if wspace:
                    tokens.append(Token(16, wspace))
                
            # catcodes 1 to 15 are straightforward
            elif c == '{':
                tokens.append(Token(1,c))   # start group
            elif c == '}':
                tokens.append(Token(2,c))   # end group
            elif c == '$':
                tokens.append(Token(3,c))   # mathmode
            elif c == '&':
                tokens.append(Token(4,c))   # alignment 
            elif c == '\n':
                tokens.append(Token(5,c))   # newline
            elif c == '#':
                tokens.append(Token(6,c))   # parameter
            elif c == '^':
                tokens.append(Token(7,c))   # superscript
            elif c == '_':
                tokens.append(Token(8,c))   # subscript 
            elif c == '':
                tokens.append(Token(9,c))   # null (empty string)
            elif c.isspace():
                tokens.append(Token(10,c))  # space 
            elif c.isalpha():
                tokens.append(Token(11,c))  # letter
            elif c == '~':
                tokens.append(Token(13,c))  # active
            elif c == '%':
                tokens.append(Token(14,c))  # comment
            elif c == '\x7f':
                tokens.append(Token(15,c))  # invalid character (delete)
            else:
                tokens.append(Token(12,c))  # everything else
        
        # include end token
        if end_token:
            tokens.append(EndToken())
        
        tokens.reverse()
        return tokens


def test_tokens():
    # s = r'\begin   {document}  \$  3   Hello \textbf   {cruel} world!  \end    {document}'
    # s = r'pre \begin{questions} \question[10] How? \question[20] Why? \end{questions} post'
    # s = r'$\alpha    + \beta$'
    # s = r'\title[short]{long}'
    s = r'pre \begin{figure*} inside \end{figure*} post'
    # s = r'Hello \textbf{world}!'
    # s = r'\begin  {center} hello \end   {center}  '

    ts = TokenStream(s)
    print(s)
    print(ts[::-1])

if __name__ == '__main__':
    test_tokens()
