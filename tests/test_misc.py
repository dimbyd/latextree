from latextree.parser.parser import Parser
import pytest

test_strings = [
    # lengths
    r'pre \setlength{\parskip}{3ex} post',
    # active characters
    r'no~break',
    # comments
    r'''%\def\bit{\itemize}
    ''',
]

@pytest.mark.parametrize("test_input", test_strings)
def test_misc(test_input):
    p = Parser()
    root = p.parse(test_input)
    assert test_input == root.chars()
