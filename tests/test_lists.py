from latextree.parser.parser import Parser
import pytest

test_strings = [
    r'pre \begin{itemize} \item First \item Second \end{itemize} post',
    r'pre \begin{itemize}\item A\item B\begin{enumerate}\item C\item D\end{enumerate}\item E\item F\end{itemize} post',
    r'pre \begin{itemize}\item A\item B\begin{itemize}\item C\item D\end{itemize}\item E\item F\end{itemize} post',
]

@pytest.mark.parametrize("test_input", test_strings)
def test_parser(test_input):
    p = Parser()
    root = p.parse(test_input)
    assert test_input == root.chars()
