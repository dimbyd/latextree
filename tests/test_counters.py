from latextree.parser.parser import Parser
import pytest

test_strings = [
    r'pre \setcounter{mycounter}{3} post',
    r'\arabic{section}\section{Intro}\arabic{section}',
    r'\thesection\section{Intro}\arabic{section}',
    r'\thefigure',
    r'\thesubsubsection',
]

@pytest.mark.parametrize("test_input", test_strings)
def test_parser(test_input):
    p = Parser()
    root = p.parse(test_input)
    assert test_input == root.chars()
