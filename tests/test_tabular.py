from latextree.parser.parser import Parser
import pytest

test_strings = [
        r'''
        \begin{tabular}{ccc} inside \end{tabular}
        ''',
        r'''
        \begin{tabular}{cccc}
        \hline
        a & b & c & d \\
        e & f & g & h \\
        \hline
        \hline
        i & j & k & l \\
        \hline
        \end{tabular}
        ''',
]

@pytest.mark.parametrize("test_input", test_strings)
def test_parser(test_input):
    p = Parser()
    root = p.parse(test_input)
    assert test_input == root.chars()
