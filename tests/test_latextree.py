import os

from latextree.parser import Parser
from latextree import LatexTree
from latextree import settings


def test_latextree():
    
    p = Parser()
    
    defs_file = 'examdef.json'
    defs_file = os.path.join(settings.EXTENSIONS_ROOT, defs_file)
    p.read_defs_file(defs_file)

    # tex_main = 'test_article/main.tex'
    tex_main = 'test_quiz/main.tex'
    tex_main = os.path.join(settings.LATEX_ROOT, tex_main)
    tree = LatexTree(tex_main)
    
    # chars test
    try:
        with open(tex_main) as f:
            src = f.read()

    except FileNotFoundError as e:
        raise Exception('File {} not found'.format(e.filename))

    assert(tree.root.chars() == src)
 

        