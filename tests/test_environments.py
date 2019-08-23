from latextree.parser.parser import Parser
import pytest

test_strings = [
    r'\begin{document}Hello world!\end{document}',
    r'pre \begin{myenv} inside \end{myenv} post',
    r'pre \begin{myenv} first \begin{myenv} inside \end{myenv} second \end{myenv} post',
    r'pre \begin{verbatim}\oops\setcounter[naughty]\end{verbatim} post',
    r'pre \begin{minipage}{\linewidth} inside \end{minipage} post',
]

@pytest.mark.parametrize("test_input", test_strings)
def test_parser(test_input):
    p = Parser()
    root = p.parse(test_input)
    assert test_input == root.chars()
