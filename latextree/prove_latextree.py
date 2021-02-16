import os
import latextree.settings as settings
from latextree.parser import Parser
from latextree.tree import LatexTree


def prove_tree_A():

    # init tree
    tree = LatexTree()

    # read defs
    defs_file = 'examdef.json'
    defs_file = os.path.join(settings.EXTENSIONS_ROOT, defs_file)
    tree.read_defs_file(defs_file)

    # parse file
    tex_file = 'test_article/main.tex'
    tex_file = os.path.join(settings.LATEX_ROOT, tex_file)
    tree.parse_file(tex_file)

    print('------------------------------')
    print(tree.write_pretty())
    print('------------------------------')
    print(tree.write_xml())
    print('------------------------------')

    # test post-processing
    tree.process_tree()
    print(tree.write_pretty())
    print(tree.numbers)
    print(tree.labels)

    # test find-by-type
    for node in tree.root.get_phenotypes(species='Mathmode'):  # list
        print(node.chars())

    # test xml-to-file
    xout = tree.write_xml()
    with open('xtree.xml', 'w') as f:
        f.write(xout)

    # # test bbq
    # bbq = tree.write_bbq(include_mathjax_header=False)
    # print(bbq)
    # with open('./output/bbq.tsv', 'w') as f:
    #     f.write(bbq)


def prove_tree_B():

    # set filename
    # tex_main = 'test_quiz/main.tex'
    # tex_main = 'test_small/main.tex'
    tex_main = 'test_misc/main.tex'
    tex_main = os.path.join(settings.LATEX_ROOT, tex_main)

    # build tree
    tree = LatexTree()
    tree.parse_file(tex_main)
    tree.pp_tree()

    print('------------------------------')
    print(tree.root.pretty_print())
    print('------------------------------')
    # print(tree.root.xml_print())
    print('------------------------------')
    print(tree.root.chars())
    print('------------------------------')

    # chars test
    with open(tex_main) as f:
        src = f.read()
        from termcolor import colored
        print('------------------------------')
        if (tree.root.chars() == src):
            print(colored('True', 'green'))
        else:
            print(colored('False', 'red'))
        print('------------------------------')

    # labels test
    for key, val in tree.labels.items():
        print('{:20} {}'.format(key, val.chars()))
    print('------------------------------')

    # numeric paths test
    # paths = tree.get_numeric_paths()
    # for key, val in paths.items():
    #     path = '.'.join([str(num) for num in val])
    #     print('{}\t{}'.format(key, path))
    # print('------------------------------')

    # # traversal test
    # print('Numbered phenotypes:')
    # for species in tree.parser.registry.numbered:
    #     phenotypes = tree.get_phenotypes(species)
    #     if phenotypes:
    #         print('\t{}: {}'.format(species, phenotypes))

    # bbq test
    # bbq = tree.write_bbq(include_mathjax_header=False)
    # print('------------------------------')
    # print(bbq)
    # print('------------------------------')
    # out_file = os.path.join(settings.PACKAGE_DIR, 'bbq.tsv')
    # with open(out_file, 'w') as f:
    #     f.write(bbq)


if __name__ == '__main__':
    #    prove_tree_A()
    prove_tree_B()
