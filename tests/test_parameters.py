from latextree.parser.parser import Parser
import pytest

test_strings = [
    r'pre \item[*]  post',
    r'pre \title[short]{Long} post',
    r'pre \textbf{hello} post',
    r'pre \textbf1 post',
    r'pre \textbf A post',
    r'pre \textit\LaTeX post',
    r'pre \textbf\$ post',
    r'pre \unknown[1] post',
    r'pre \points[3] post',
]

@pytest.mark.parametrize("test_input", test_strings)
def test_parser(test_input):
    p = Parser()
    root = p.parse(test_input)
    assert test_input == root.chars()
