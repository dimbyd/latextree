from latextree.parser.parser import Parser
import pytest

test_strings = [
    r'pre \center inside \endcenter post',
    r'pre \itemize \item First \item Second \enditemize post',
    r'pre \center inside \endcenter post',
    r'pre \itemize \item a \item b \enditemize post',
]

@pytest.mark.parametrize("test_input", test_strings)
def test_parser(test_input):
    p = Parser()
    root = p.parse(test_input)
    assert test_input == root.chars()
