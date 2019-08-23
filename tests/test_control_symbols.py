from latextree.parser.parser import Parser
import pytest

test_strings = [
    r'pre \$100 post',
    r'pre \$   100 post',
    r'pre \textbf  {hello \$y}  post',
    r'pre \\[2ex] post',
    r'pre \\  [2ex] post',
    r'pre Hell\"{o}  post',
    r'pre \$3 mid \$ 3 post',
    r'pre \^{o} and \^o post'
]

@pytest.mark.parametrize("test_input", test_strings)
def test_parser(test_input):
    p = Parser()
    root = p.parse(test_input)
    assert test_input == root.chars()
