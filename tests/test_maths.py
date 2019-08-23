from latextree.parser.parser import Parser
import pytest

test_strings = [
    r'pre $\alpha+\beta$ post',
    r'pre \(\alpha+\beta\) post',
    r'pre \[\alpha+\beta\] post',
    r'pre $$\alpha+\beta$$ post',
    r'pre $\int_0^1x^2\dx=\frac{1}{3}$ post',
    r'pre \[\int_{-\pi}^{\pi} x^3\cos(x)\,dx\] post',
    r'pre $E = mc^2$ mid $\alpha+\beta=\gamma$ post',
    r'pre \begin{align} x & = a + b \\ y & = c + d\end{align} post',
    r'pre \begin{equation}\label{eq:euler} blah \end{equation} post',

    r'pre $\mathbf{x}$ post',
    r'$\sum_{i=1}^n \frac{1}{n^2} = \frac{\pi}{6}$',
    r'$$\sum_{i=1}^n \frac{1}{n^2} = \frac{\pi}{6}$$',
    r'\begin{equation}e^{i\pi}+1=0\end{equation}',
    r'\begin{equation*}S=k\log W\end{equation*}',
]

@pytest.mark.parametrize("test_input", test_strings)
def test_parser(test_input):
    p = Parser()
    root = p.parse(test_input)
    assert test_input == root.chars()
