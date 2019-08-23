from latextree.parser.parser import Parser
import pytest

test_strings = [
    r'\begin{figure*} Hello \end{figure*}',
    r'\vspace*{2ex}',
    r'\\*',
]

@pytest.mark.parametrize("test_input", test_strings)
def test_parser(test_input):
    p = Parser()
    root = p.parse(test_input)
    assert test_input == root.chars()
