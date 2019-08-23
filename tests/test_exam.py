from latextree.parser.parser import Parser
from latextree import settings
import os
import pytest

test_strings = [
    r'''
    pre 
    \begin{questions} 
    \question[10] How? 
    \question[20] Why? 
    \end{questions} 
    post
    ''',
    r'''
    \begin{questions}
    \question[5] $1 + 1$ \ans{2}
    \question[5] $2 + 2$ \ans{3}
    \end{questions}
    ''',
    r'''
    \begin{questions}
    \question 
    The product of an odd and even function is 
    \begin{choices}
    \correctchoice Odd
    \choice Even
    \choice Neither
    \end{choices}
    \end{questions}
    ''',
    r'''
    \begin{choices}
    \choice dog 
    \correctchoice cat 
    \choice mouse
    \end{choices}
    ''',

]

defs_file = os.path.join(settings.EXTENSIONS_ROOT, 'examdef.json')


@pytest.mark.parametrize("test_input", test_strings)
def test_exam(test_input):
    print(defs_file)
    p = Parser()
    p.read_defs_file(defs_file)
    root = p.parse(test_input)
    assert test_input == root.chars()
