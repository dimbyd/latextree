# ptest.py (package test)

import os
from termcolor import colored

from parser import Parser


def test_parse():

    test_strings = [
        # r'\bibliography{test.bib}',
        # r'\setlength{\parskip}{2ex}',
        r'Hello world!',
        r'pre \textbf{Hello} post',
        r'pre \chapter[intro]{Introduction} post',
        r'pre pre \$ 3 post post',
        r'pre $E=mc^2$ post',    
        r'pre \question[3] post',
        r'pre \[\sum x_i = 1\] post',
        r'pre \center inside \endcenter post',
        r'pre \begin {center}hello\end {center} post',
        r'pre \begin{tabular}{c} hello \end{tabular} post',
        r'pre \begin{tabular}{cc}\hline a & b \\[2ex] \hline c & d \\ \hline \end{tabular} post',
        r'pre \begin   {itemize}\item a \item b\end     {itemize} post',
        r'pre \itemize   \item    a   \item   b   \enditemize   post',
        r'pre \chapter*{Intro} post',
        r'pre \begin{figure*} inside \end{figure*} post',
        r'pre \newenvironment{myenv}{hello}{bye} \begin{myenv} inside \end{myenv} post',
        r'\newtheorem{theo}{Theorem}'
        r'\newtheorem{theo}{Theorem}[section]\begin{theo} inside \end{theo}', 
        r'\def\strong[1]{\textbf{#1}}',
        r'\def\logo{\LaTeX}',
        r'\def\show[1]{\begin{center}#1\end{center}}',
        r'\def\emph[1]{pre \textbf{#1} \LaTeX post} \emph{hello}',
        r'\def\doit{pre \begin{center}inside\end{center} post} \doit',
        r'pre \newcommand{\hello}[1]{Hi #1} \hello{Bob} post',
        # this is too hard!!
        # r'''
        # \def\bit{\itemize}
        # \def\eit{\enditemize}
        # \bit \item a \item b \eit
        # ''',
        r'\question[10]',
        r'''
        pre 
        \begin{questions} 
        \question[10] How? 
        \question[20] Why? 
        \end{questions} 
        post
        ''',
        r'pre \includegraphics{mypic.png} post',
        r'\graphicspath{{figures/}{./images/}}',
        r'pre \input{anotherfile.tex} post',
        r'pre \chapter{Intro}Hello\section{First}blah\section{Second}blah\chapter*{Dummy}Dumbo\chapter{Background}\section*{blue}hello\section{bird}bye Blah blah post',
        # r'pre \paragraph{A}a\subparagraph{AA}aa post',
        # r'\caption{Three figures using \texttt{subfigure}.\label{fig:setops-subfig}}',
        # r'pre {\tt latextree} post',
        r'pre m\^{o}r post',
        r'pre \'e\`e\^w\"o post',
        r'pre \'e \`e \^w \"o post',
        r'first {\bf second {\it third} fourth} fifth',
        r'\arabic{section}\section{Intro}\arabic{section}',
        r'\thesection\section{Intro}\arabic{section}',
        r'''
        \newtheorem{theo}{Theorem}[section]
        \newtheorem{lem}[theo]{Lemma}
        \begin{theo}statement of theorem\end{theo}
        \begin{lem}statement of lemma\end{lem}
        ''',
        r'''
        \begin{minipage}{\linewidth}
        \centering
        Some text
        \end{minipage}
        ''',
        r'\arabic{chapter}',
        r'''
        pre
        % \noshow 1
        % noshow 2
        post
        ''',
        r'''
\begin{document}\label{doc:testdoc}
%\maketitle
%\tableofcontents
\input{_abstract}
%\input{_intro}
%\input{_sections}
\end{document}
'''
    ]

    # iterate over test strings
    numerrors = 0
    for i, s in enumerate(test_strings):
        print('TEST {}'.format(i))
        print(s)
        p = Parser()
        root = p.parse(s)
        # print('------------------------------')
        print(root.pretty_print())
        print('------------------------------')
        # print(root.xml_print())
        # print('------------------------------')
        # print(root.chars())
        # print('------------------------------')
        # print(root.chars(non_breaking_spaces=True))
        # print('------------------------------')
        # print(root.chars(insert_strict_braces=True))
        print('------------------------------')
        print(s)
        print(root.chars())
        print('------------------------------')
        if (root.chars() == s):
            print(colored('True', 'green'))
        else:
            print(colored('False', 'red'))
            numerrors += 1
        # print(p.counters)
        # print(p.registry.names)
        # for k, v in p.registry.block_declarations.items():
        #     print('{:20}{}'.format(k,v))
        # print('------------------------------')

    print('------------------------------')
    print('END TEST: inversion errors: {} ({}).'.format(numerrors, i))
    print('------------------------------')

def test_parse_file():
    tex_main = 'tex/test_small/main.tex' 
    tex_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tex_main = os.path.join(tex_root, tex_main)
    print('main file: {}'.format(tex_main))
    p = Parser()
    root = p.parse_file(tex_main)
    print('------------------------------')
    print(root.pretty_print())
    # print('------------------------------')
    # print(root.xml_print())
    print('------------------------------')
    print(root.chars())
    print('------------------------------')

if __name__ == '__main__':
    test_parse()
    # test_parse_file()
