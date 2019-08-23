# names.py
r'''
Taken from the (built-in) babel files.
Perhaps we can do something like:
    \newtheorem{exc}{\en Exercise \cy Ymarfer}
Test it!!

e.g. for new floats:
\floatname{video}{Video}
then
\renewcommand{\floatname}{Fideo}

'''
from collections import namedtuple

TexName = namedtuple('TexName', 'en cy')

tex_names = {
    'prefacename':      TexName(en='Preface', cy='Rhagair'),
    'refname':          TexName(en='References', cy='Cyfeiriadau'),
    'abstractname':     TexName(en='Abstract', cy='Crynodeb'),
    'bibname':          TexName(en='Bibliography', cy='Llyfryddiaeth'),
    'chaptername':      TexName(en='Chapter', cy='Pennod'),
    'sectionname':      TexName(en='Section', cy='Adran'),
    'subsectionname':   TexName(en='Subection', cy='Isdran'),
    'subsubsectionname':TexName(en='Subsubection', cy='Isisadran'),
    'paragraphname':    TexName(en='Paragraph', cy='Paragraff'),
    'subparagraphname': TexName(en='Subparagraph', cy='Isbaragraff'),
    'appendixname':     TexName(en='Appendix', cy='Atodiad'),
    'contentsname':     TexName(en='Contents', cy='Cynnwys'),
    'listfigurename':   TexName(en='List of Figures', cy='Rhestr Ddarluniau'),
    'listtablename':    TexName(en='List of Tables', cy='Rhestr Dablau'),
    'indexname':        TexName(en='Index', cy='Mynegai'),
    'figurename':       TexName(en='Figure', cy='Darlun'),
    'tablename':        TexName(en='Table', cy='Tabl'),
    'partname':         TexName(en='Part', cy='Rhan'),
    'enclname':         TexName(en='encl', cy='amgae\"edig'),
    'ccname':           TexName(en='cc', cy='cop\\"\\i au'),
    'headtoname':       TexName(en='To', cy='At'),
    'pagename':         TexName(en='page', cy='tudalen'),
    'seename':          TexName(en='see', cy='gweler'),
    'alsoname':         TexName(en='see also', cy='gweler hefyd'),
    'proofname':        TexName(en='Proof', cy='Prawf'),
    'glossaryname':     TexName(en='Glossary', cy='Rhestr termau'),
}

def main():
    for tex_name in tex_names.values():
        print('{:20s} {:10s}'.format(tex_name.en, tex_name.cy))

if __name__ == '__main__':
    main()
