from latextree.parser.parser import Parser
import pytest

test_strings = [
    r'\newtheorem{lemma}{Lemma}[theorem]',
    r'\newenvironment{myenv}{pre}{post}',
    r'\newcommand{\strong}[1]{\textbf{#1}}',    
    r'\newcommand{\nice}[1]{\textit{#1}}',
    r'\renewcommand{\emph}[1]{\textbf{#1}}',
    r'\def\hello{shw mae}',
    r'\def\strong[1]{\textbf{#1}}',
    r'\newenvironment{myenv}{}{} \begin{myenv}inside\end{myenv}',
    r'\newenvironment{myenv}[1]{\textbf{start #1}}{\textbf{finish}} \begin{myenv}{twat}inside\end{myenv}',
    r'\newenvironment{myenv}[2]{\textbf{start #1--#2}}{\par\textbf{finish}}',
    r'\newtheorem{theo}{Theorem}\begin{theo} inside \end{theo}',
    r'\newtheorem{theo}{Theorem}[section]\begin{theo} inside \end{theo}',
    r'\newtheorem{lem}[theo]{Lemma}\begin{theo} inside \end{theo}\begin{lem} hello \end{lem}',

    r'\newcommand{\hello}[1]{Hi #1} \hello{Bob}',
    r'\newcommand{\hello}[1]{Hi #1} \hello{Bob $\alpha=\beta$}',
    r'\newcommand{\isa}[2]{#1 is a #2} \isa{Bingo}{dog}',
 
]

@pytest.mark.parametrize("test_input", test_strings)
def test_parser(test_input):
    p = Parser()
    root = p.parse(test_input)
    assert test_input == root.chars()
