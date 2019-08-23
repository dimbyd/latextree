from latextree.parser.parser import Parser
import pytest

test_strings = [
    r'{pre \bf hello \it world \normalfont post}',
    r'first \raggedleft second \centering third \raggedright fourth',
    r'first \small second \large third \normalsize fourth',
    r'{pre zero {\bf pre first {\it second} post first} post zero}',
]

@pytest.mark.parametrize("test_input", test_strings)
def test_parser(test_input):
    p = Parser()
    root = p.parse(test_input)
    assert test_input == root.chars()
