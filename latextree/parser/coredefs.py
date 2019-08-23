# coredefs.py
r'''
This file contains the dictionary `defs' which has the following keys:

Families:
1. `commands'           argument definitions for commands
2. `environments':      argument definitions for environments
3. `declarations':      argument definitions for declarations

Stop token definitions:
4. `blocks':      keyed on species: `chapter',  `item', etc.
5. `modes':       keyed on genus: Alignment, FontStyle, FontSize, Language

Counter definitions:
6. `numbered'           primary numbered species (and reset counters)
7. `numbered_like':     species numbered with a primary numbered species (e.g. lemma 1, theorem 2, ...)
8. `marker_formats':    how numbers are displayed (e.g. by \thechapter)

The Family classes are divided into Genera, and each species is allocated to 
a specific Genus class. The Genus names are mostly arbitrary and are passed through to templates. 
The Genus names are capitalized which helps to distingish them from species names, 
which are taken from the corresponding latex command name and so are mostly lower case.

TODO: some species/genus/argument/character names are hard-wired in the parser
    Custom: def, newcommand, newenvironment, ...
    Number: arabic, alph, roman, ...
    Verbatim: verbatim
We need to prevent these from being overwrriten by a custom definitions file.

Declarations
    "Declarations produce neither text nor space but either 
    affect the way LATEX prints the following text or provide 
    information for later use. Font size changes are an example 
    of declarations. \large will cause any text that follows to 
    appear in a larger type size. Declarations are often used 
    within a group to limit their scope."
    Note: for every declaration Latex always provides an environment 
    of the same name eg
      \begin{bf}hello\end{bf} 
    works so do we need to specify these in the env definitions too?
    
    1. For mode declarations eg \bf, the parser creates the corresponding
      Declaration.FontStyle:bf 
    node then process tokens until the next mode declaration of
    genus 'FontStyle' or another stop tokenis encountered, eg
       (0,'sc'), (2, '}') or (0,'end')
    Tex-style environments work in the same way, they just define blocks ...

    2. TODO: directive declarations change the global parameters
        Counters: eg \setcounter{section}
            - change the value of the counter on-the-fly
        Lengths: eg \setlength{\parskip}{1em}:  
            - record for write functions (in registry.lengths say)
'''

r'''
% \CharacterTable
%  {Upper-case    \A\B\C\D\E\F\G\H\I\J\K\L\M\N\O\P\Q\R\S\T\U\V\W\X\Y\Z
%   Lower-case    \a\b\c\d\e\f\g\h\i\j\k\l\m\n\o\p\q\r\s\t\u\v\w\x\y\z
%   Digits        \0\1\2\3\4\5\6\7\8\9
%   Exclamation   \!     Double quote  \"     Hash (number) \#
%   Dollar        \$     Percent       \%     Ampersand     \&
%   Acute accent  \'     Left paren    \(     Right paren   \)
%   Asterisk      \*     Plus          \+     Comma         \,
%   Minus         \-     Point         \.     Solidus       \/
%   Colon         \:     Semicolon     \;     Less than     \<
%   Equals        \=     Greater than  \>     Question mark \?
%   Commercial at \@     Left bracket  \[     Backslash     \\
%   Right bracket \]     Circumflex    \^     Underscore    \_
%   Grave accent  \`     Left brace    \{     Vertical bar  \|
%   Right brace   \}     Tilde         \~}
'''

# Active characters 
# subclassed from ControlSequence (because they can have arguments e.g. "o in babel german)
# _ and ^ are also active characters (?)
# active_chars = ['~']

# Control character names based on the \CharacterTable
# Classes corresponsing to control characters are named,
# the character itself is stored as an attribute (symbol).
# This is to avoid class names such as '[' or '!' because
# xml does not accept such element names.
character_names = {
    '!': 'Exclamation',
    '$': 'Dollar',
    "'": 'Acute',
    '*': 'Asterisk',
    '-': 'Minus',
    ':': 'Colon',
    '=': 'Equals',
    '@': 'At',
    ']': 'Right_bracket',
    '`': 'Grave',
    '}': 'Right_brace',
    '"': 'Double_quote',
    '%': 'Percent',
    '(': 'Left_paren',
    '+': 'Plus',
    '.': 'Point',
    ';': 'Semicolon',
    '>': 'Greater_than',
    '[': 'Left_bracket',
    '^': 'Circumflex',
    '{': 'Left_brace',
    '~': 'Tilde',
    '#': 'Hash',
    '&': 'Ampersand',
    ')': 'Right_paren',
    ',': 'Comma',
    '/': 'Solidus',
    '<': 'Less_than',
    '?': 'Question_mark',
    '\\': 'Backslash',
    '_': 'Underscore',
    '|': 'Vertical_bar',
}

# main definitions directory
defs = {

    # ------------------------------
    # active characters
    'active': {
        'default': [
            '~',            # non-breaking space
        ],
        # 'german': [
        #     '"{char}',      # umulat (see babel)
        # ],
    },

    # ------------------------------
    # commands
    'commands': {
        'Accent': [
            '"{char}',    # umulat      \"o
            "'{char}",    # acute       \'o
            '`{char}',    # grave       \`o
            '^{char}',    # circumflex  \^o
            '.{char}',    # dot over    \.o
            '={char}',    # commandn      \=o
            'c{char}',    # cedilla
            'k{char}',    # ogonek
            'b{char}',    # bar under
            'd{char}',    # dot under
            'r{char}',    # ring over
            'u{char}',    # breve over
            'v{char}',    # caron over
        ],
        'Bibtex': [
            'bibliographystyle{style}',
            'bibliography{bibtex_file}',
        ],
        'Box': [
            'fbox{contents}',
        ],
        'Caption': [
            'caption[*][lst-entry]{caption_text}',
        ],
        'FontStyle': [
            'emph{text}',
            'textrm{text}',
            'textit{text}',
            'textbf{text}',
            'textsl{text}',
            'textsf{text}',
            'texttt{text}',
            'textsc{text}',
            'texttt{text}',
            'underline{text}',
        ],
        'Footnote': [
            'footnote{text}',
            'mpfootnote{text}',
        ],
        'Horizontal': [
            ' ',    # space             \<space> 
            ',',    # half-space        \, 
            '!',    # half-space back   \!
            'quad',
            'qquad',
            'noindent',
            'mbox{contents}',
            'hfill',
        ],
        'Input': [
            'input{file}',
            'include{file}',
        ],
        'Item': [
            'item[marker]',
            'bibitem[marker]{key}',
        ],
        'Label': [
            'label{key}',
        ],
        'Macro': [
            'def{name}[numargs]{def}',
            'newcommand{name}[numargs][opt]{def}',
            'renewcommand{name}[numargs][opt]{def}',
            'providecommand{name}[numargs][opt]{def}',
            'newenvironment{name}[numargs]{begdef}{enddef}',
            'renewenvironment{name}[numargs]{begdef}{enddef}',
            'newtheorem{name}[numbered_like]{caption}[numbered_within]',
        ],
        'Maths': [
            '[',    # begin displaymath ($$)
            ']',    # end displaymath ($$)
            '(',    # begin mathmode ($)
            ')',    # end mathmode ($)
        ],        
        'Misc': [
            'addtocontents{file}{text}',
            'addcontentsline{file}{sec_unit}{entry}',
            'address{return_address}',
        ],
        'Numeral': [
            'arabic{counter}',
            'alph{counter}',
            'Alph{counter}',
            'roman{counter}',
            'Roman{counter}',
            'fnsymbol{counter}',
        ],
        'Preamble': [
            'title[short_title]{title}',
            'author{names}',
            'date{date}',
            'usepackage[options]{name}',
            'documentclass[options]{name}',
        ],
        'Section': [
            'chapter[*][short-title]{title}',
            'section[*][short-title]{title}',
            'subsection[*][short-title]{title}',
            'subsubsection[*][short-title]{title}',
            'paragraph[*][short-title]{title}',
            'subparagraph[*][short-title]{title}',
        ],
        'Special': [
            '$',    # dollar
            '&',    # ampersand
            '%',    # percent
            '{',    # left brace
            '}',    # right brace
            '_',    # underscore
        ],    
        'Symbol': [
            'i',            # dotless i
            'j',            # dotless j
            'l',            # barred l 
            'o',            # slashed o
            'dag',          # dagger
            'ddag',         # double dagger
            'S',            # section
            'P',            # paragraph
            'copyright',    # copyright
            'pounds',       # sterling
        ],
        'Tabular': [
            '\\[*][length]',   # line break for tabular
        ],
        'Vertical': [
            'par', 
            'smallskip', 
            'bigskip',
            'vspace[*]{length}',
        ],
        'Vspace': [
            'addvspace{length}',
            'bigskip',
        ],
        'Xref': [
            'ref{key}',
            'cite[text]{key_list}',
            'pageref{key}',
            'eqref{key}',
        ],
        'Camnotes': [   # move to camnotes.json
            'includevideo[*][options]{url}',
        ],
        'Cambi': [      # move to cambi.json
            'bi', 'cy', 'en', 'fr', 'de',
            'eng{text}',
            'cym{text}',
            'wel{text}',
        ],
        'Graphicx': [    # move to graphicx.json
            'includegraphics[*][options]{file}',
            'graphicspath{paths}',
            'DeclareGraphicsExtensions{ext_list}',
        ],
        'Hyperref': [   # move to hyperref.json (and have separate genera 'xref' for internal and 'href' for external)
            'autoref{key}',
            'nameref{key}',
            'hyperref[key]{text}',
            'url{url}',
            'href{url}{text}',
        ],
        'Lipsum': [     # move to lipsumdef.json       
            'lipsum[num]',
        ],
    },

    # ------------------------------
    # environments
    'environments': {
        
        'Document': [
            'document',
        ],
        'Tabular': [
            'tabular[pos]{cols}',
            'tabular*{width}[pos]{cols}',
        ],
        'List': [
            'list{label}{spacing}',
            'itemize[options]',
            'enumerate[options]',
            'description[options]',
            'trivlist',
            'thebibliography{widest_label}',
        ],
        'Float': [
            'table[*][options]',
            'figure[*][options]',
            'video[*][options]',    # should be in camnotesdef.json
        ],
        'Picture': [
            'picture[options]',
            'tikzpicture[options]',
            'pspicture[options]',
        ],
        'Displaymath': [
            'displaymath',
            'equation[*]',
            'eqnarray[*]',
            'align[*]',
            'gather[*]',
        ],
        'Verbatim': [
            'verbatim',
            'lstlisting',
        ],
        'Align': [
            'center',
            'flushleft',
            'flushright',
        ],
        'Box': [
            'abstract[options]',
            'quote[options]',       
            'minipage{width}[options]',
        ],
        'Cambi': [ # move to cambidef.json
            'english',
            'cymraeg',
            'welsh',
        ]

    },

    # ------------------------------
    # declarations
    'declarations': {

        'Counters': [
            'newcounter{name}[master]',
            'addtocounter{counter}{value}',
            'setcounter{counter}{value}',
            'usecounter{counter}',
            'value{counter}',
            'counterwithin{name}{master}',
            'counterwithout{name}{master}',
        ],
        'Length': [
            'addtolength{name}{len}',
            'baselineskip',
            'baselinestretch',
        ],
        'Alignment': [
            'centering',    # eqiv. to center env
            'raggedleft', # eqiv. to flushright env 
            'raggedright',  # eqiv. to flushleft env
        ],
        'FontStyle': [
            'rm', 'rmfamily',
            'sf', 'sffamily',
            'bf', 'bfseries',
            'it', 'itshape',
            'sl', 'slshape',
            'sc', 'scshape',
            'tt', 'ttshape',
            'em', 
            'normalfont',
        ],
        'FontSize': [
            'tiny',
            'scriptsize',
            'footnotesize',
            'small',
            'normalsize',
            'large',
            'Large',
            'LARGE',
            'huge',
            'Huge',
        ],
        'Language': [   # move to cambi.json
            'bi', 
            'cy', 
            'en', 
            'fr', 
            'de',
        ], 
    },

    # ------------------------------
    # block_declarations (stop tokens are all cmds of the same genus)
    'block_declarations': [
        'Alignment',
        'FontStyle',
        'FontSize',
        'Language',
    ],

    # ------------------------------
    # stop tokens for block commands 
    'block_commands': {
        "chapter":          ["document"],
        "section":          ["chapter", "document"],
        "subsection":       ["section", "chapter", "document"],
        'subsubsection':    ["subsection", "section", "chapter", "document"],
        'paragraph':        ["subsubsection", "subsection", "section", "chapter", "document"],
        'subparagraph':     ["paragraph", "subsubsection", "subsection", "section", "chapter", "document"],
        "item":             ["itemize", "enumerate", "list"],
        "bibitem":          ["thebibliography"],
    },

    # ------------------------------
    # numbered species and master counters
    'numbered': {
        'chapter':          'document',
        'section':          'chapter',
        'subsection':       'section',
        'subsubsection':    'subsection',
        'paragraph':        'subsubsection',
        'subparagraph':     'paragraph',
        'page':             'document',
        'equation':         'chapter',
        'figure':           'chapter',
        'table':            'chapter',
        'footnote':         'chapter',
        'mpfootnote':       'chapter',
        'enumi':            'document',
        'enumii':           'enumi',
        'enumiii':          'enumii',
        'enumiv':           'enumiii',
        'thebibliography':  'document',
        'bibitem':          'thebibliography',
        # package-specific (should be moved)
        'subfigure':        'figure',
        'subtable':         'table',
        'video':            'chapter',
    },

    # 'counters': {
    #     'enumerate':        'document',
    #     'enumi':            'enumerate',
    #     'enumii':           'enumi',
    #     'enumiii':          'enumii',
    #     'enumiv':           'enumiii',
    #     'thebibliography':  'document',
    #     'bibitem':          'thebibliography',
    # },

    # ------------------------------
    # shared counters
    'numbered_like': {
        'eqnarray':     'equation',
        'align':        'equation',
    },

    # ------------------------------
    # default numeric labels
    # TODO: choose relative to documentclass
    'marker_formats': {
        # 'chapter':           '\\arabic{chapter}.',
        'chapter':           '',
        'section':           '\\arabic{section}',
        # 'section':           '\\Roman{section}',
        'subsection':        '\\thesection.\\arabic{subsection}',
        # 'subsection':        '\\thesection.\\alph{subsection}',
        'subsubsection':     '\\thesubsection.\\arabic{subsubsection}',
        'paragraph':         '\\thesubsubsection.\\arabic{paragraph}',
        'subparagraph':      '\\theparagraph.\\arabic{subparagraph}',
        'equation':          '\\thesection.\\arabic{equation}',    
        'figure':            '\\arabic{figure}',    
        'subfigure':         '\\alph{subfigure}',    
        'table':             '\\arabic{table}',    
        'subtable':          '\\alph{subtable}',
        'page':              '\\arabic{page}',
        'footnote':          '\\arabic{footnote}',
        'mpfootnote':        '\\alph{footnote}',
        'enumi':             '\\arabic{enumi}.',
        'enumii':            '(\\alph{enumii})', 
        'enumiii':           '\\roman{enumiii}.',
        'enumiv':            '\\Alph{enumiv}.',
    },    
# names (as found in babel files)
    'names': {
        'videoname': {
            'en':   'Video',
            'cy':   'Fideo',
        },
        'prefacename': {
            'en':   'Preface',
            'cy':   'Rhagair',
        },
        'refname': {          
            'en':   'References',
            'cy':   'Cyfeiriadau',
        },
        'abstractname': {    
            'en':   'Abstract',
            'cy':   'Crynodeb',
        },
        'bibname': {         
            'en':   'Bibliography',
            'cy':   'Llyfryddiaeth',
        },
        'chaptername': {     
            'en':   'Chapter',
            'cy':   'Pennod',
        },
        'sectionname': {     
            'en':   'Section',
            'cy':   'Adran',
        },
        'subsectionname': {  
            'en':   'Subection',
            'cy':   'Isdran',
        },
        'subsubsectionname': {
            'en':   'Subsubection', 
            'cy':   'Isisadran',
        },
        'paragraphname': {   
            'en':   'Paragraph',
            'cy':   'Paragraff',
        },
        'subparagraphname': {
            'en':   'Subparagraph', 
            'cy':   'Isbaragraff',
        },
        'appendixname': {    
            'en':   'Appendix',
            'cy':   'Atodiad',
        },
        'contentsname': {    
            'en':   'Contents',
            'cy':   'Cynnwys',
        },
        'listfigurename': {  
            'en':   'List of Figures',
            'cy':   'Rhestr Ddarluniau',
        },
        'listtablename': {   
            'en':   'List of Tables',
            'cy':   'Rhestr Dablau',
        },
        'indexname': {       
            'en':   'Index',
            'cy':   'Mynegai',
        },
        'figurename': {      
            'en':   'Figure',
            'cy':   'Darlun',
        },
        'tablename': {       
            'en':   'Table',
            'cy':   'Tabl',
        },
        'partname': {        
            'en':   'Part',
            'cy':   'Rhan',
        },
        'enclname': {        
            'en':   'encl',
            'cy':   'amgae\"edig',
        },
        'ccname': {          
            'en':   'cc',
            'cy':   'cop\\"\\i au',
        },
        'headtoname': {      
            'en':   'To',
            'cy':   'At',
        },
        'pagename': {        
            'en':   'page',
            'cy':   'tudalen',
        },
        'seename': {         
            'en':   'see',
            'cy':   'gweler',
        },
        'alsoname': {        
            'en':   'see also',
            'cy':   'gweler hefyd',
        },
        'proofname': {       
            'en':   'Proof',
            'cy':   'Prawf',
        },
        'glossaryname': {    
            'en':   'Glossary',
            'cy':   'Rhestr termau',
        },
    },
}



# ==============================
# mathmode (not currently used)
# If we rely on MathJax to render mathmode elements, then provided the reconstruction 
# via chars() is faithful we can recover the source and place this in the output file,
# which means we can avoid defining mathmode commands explicitly.
# One day we might want output in MathML format or similar ...
#
# ... so here are some anyway!
# ==============================
mathmode_defs = {
    
    'commands': {
        'accents': [
            'hat{char}',
            'widehat{chars}',
            'check{char}',
            'tilde{char}',
            'widetilde{chars}',
            'acute{char}',
            'grave{char}',
            'dchar{o}',
            'ddchar{o}',
            'breve{char}',
            'bar{char}',
            'vec{char}',
        ],
        'dots': [
            'cdots', 'ddots', 'ldots', 'vdots',
        ],
        'font': [
            'mathrm{char}',
            'mathit{char}',
            'mathbf{char}',
            'mathcal{char}',
            'boldmath',
            'unboldmath',
        ],
        'misc': [
            'displaystyle',
            'scriptstyle',
            'backslash',
            'frac{num}{den}',
            'text{text}',
        ],
        'tags': [           # amsmath
            'tag{key}',
        ],
    },
    
    'environments': {
        'tabular': [
            'array[pos]{cols}',
            'cases',
        ],
    },

    'symbols':  {
        'greek': [
            'alpha',   
            'beta',   
            'gamma',   
            'delta',   
            'epsilon',   
            'varepsilon', 
            'zeta',   
            'eta',   
            'theta',   
            'vartheta', 
            'iota',   
            'kappa',   
            'lambda',   
            'mu',   
            'nu',   
            'xi',   
            'pi',   
            'varpi', 
            'rho',   
            'varrho', 
            'sigma',   
            'varsigma', 
            'tau',   
            'upsilon',   
            'phi',   
            'varphi', 
            'chi',   
            'psi',   
            'omega',   
            'Gamma', 
            'Delta',   
            'Theta',   
            'Lambda',   
            'Xi',   
            'Pi',   
            'Sigma',   
            'Upsilon',   
            'Phi',   
            'Psi',   
            'Omega',   
        ],
        'other': [
            'aleph',
            'hbar',
            'imath',
            'jmath',
            'ell',
            'wp',
            'Re',
            'Im',
            'prime',
            'nabla',
            'surd',
            'angle',
            'forall',
            'exists',
            'backslash',
            'partial',
            'infty',
            'triangle',
            'Box',
            'Diamond',
            'flat',
            'natural',
            'sharp',
            'clubsuit',
            'diamondsuit',
            'heartsuit',
            'spadesuit',
        ],
    },
}