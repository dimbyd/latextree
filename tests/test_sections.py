from latextree.parser.parser import Parser
import pytest

test_strings = [
    r'Hello\section[one]{First section}Welcome\section[two]{Second section}Goodbye',
    r'A\chapter{B}C\section{D}E\subsection{F}G\section{H}I\chapter{J}K',
    r'pre \section[intro]{Introduction to $E=mc^{2+\epsilon}$} post',
    r'\chapter{Introduction}\label{ch:intro} Hello \chapter{Background}\label{ch:back} Goodbye',
    r'\chapter{Introduction}\label{ch:intro} Hello \section{Shw mae} helo \chapter{Background} background Goodbye',
]

@pytest.mark.parametrize("test_input", test_strings)
def test_parser(test_input):
    p = Parser()
    root = p.parse(test_input)
    assert test_input == root.chars()
