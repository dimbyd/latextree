# tree.py
# pylint: disable=no-member
r'''
The main LatexTree class
Initialized from a string or file name.

Methods
    tree.write_chars()      Recover Latex source code (for testing) 
    tree.write_pretty()     Native output format (see node.py)
    tree.write_xml()        Uses the `lxml` package
    tree.write_bbq()        For blackboard questions
'''
import sys


import pprint as pp
from latextree.parser.misc import parse_kv_opt_args, parse_length
from latextree.parser import Parser
from latextree.reader import read_latex_file
import sys
import os
# base_dir = os.path.dirname(os.path.abspath(__file__)) # this directory
# pars_dir = os.path.join(base_dir, 'parser')
# sys.path.insert(0, pars_dir)
# print ('sys.path is: {}'.format(sys.path))

from latextree.settings import LATEX_ROOT, EXTENSIONS_ROOT, LOG_ROOT, mathjax_source

import logging
log = logging.getLogger(__name__)

logging.basicConfig(
    filename=os.path.join(LOG_ROOT, 'latextree.log'),
    # format = '%(asctime)s:%(levelname)8s:%(name)8s:%(funcName)20s:%(lineno)4s %(message)s',
    format='%(levelname)8s:%(name)8s:%(funcName)20s:%(lineno)4s %(message)s',
    level=logging.DEBUG,
)
log.setLevel(logging.INFO)


class LatexTree():
    r'''
    Document object model for Latex
    The tree itself is accessed via the `root' node.
    Fields:
        `tex_main': main input file (absolute path)
        `root': Node type
        `preamble': map of selected nodes extracted from preamble e.g. {title: Group(), ...}
        `static': dict in the format {label: file}

    The name of an image object is its file name
        - \includegraphics{mypic.png}
    is recorded as
        - key='mypic.png'   
    If \graphicspath{{./figures/}} is set
        - key='./figures/mypic.png'
    etc.
    '''

    def __init__(self, tex_main=None):

        # init parser (why is this a field?)
        self.parser = Parser()

        # init tree (single)
        self.tex_main = None    # record main file name

        # for passing to templates
        self.preamble = {}      # selected document properties extracted from root node
        self.images = {}        # image source files (keyed on file name)

        # read extensions (custom definitions)
        for ext_file in os.listdir(EXTENSIONS_ROOT):
            if ext_file.endswith(".json"):
                log.info('Reading definitions from {}'.format(ext_file))
                ext_file = os.path.join(EXTENSIONS_ROOT, ext_file)
                self.read_defs_file(ext_file)

    def read_defs_file(self, defs_file):
        self.parser.read_defs_file(defs_file)

    # info
    def pretty_print(self):
        print('--------------------')
        print(self)
        # for key, val in self.preamble.items():
        #     print('\t{:16}:{}'.format(key, val.chars()))
        print('--------------------')

    # parse functions
    def parse(self, s):
        self.root = self.parser.parse(s)
        self.registry = self.parser.registry
        self.pp_tree()

    def parse_file(self, tex_main):
        self.tex_main = os.path.join(LATEX_ROOT, tex_main)
        self.root = self.parser.parse_file(tex_main)
        self.registry = self.parser.registry
        self.pp_tree()

    # post-processing functions
    def pp_tree(self):
        """Extract information for passing to write functions and templates.

        Question: how much of this should be done here, and how much in latex2html.py?

        """
        if not self.root:
            return
        self.pp_document()
        self.pp_preamble()
        self.pp_sections()
        self.pp_labels()
        self.pp_toc()
        self.pp_image_files()
        self.pp_widths()

    def pp_document(self):
        '''Extract document element if any.'''
        if any([child.species == 'document' for child in self.root.children]):
            self.doc_root = next(
                (child for child in self.root.children if child.species == 'document'), None)

    def pp_sections(self):
        """Tree search (DFS) for Level-1 chapters or sections."""
        if self.doc_root:
            self.chapters = self.get_phenotypes('chapter')
            self.sections = []
            if not self.chapters:
                self.sections = self.get_phenotypes('section')

    def pp_preamble(self):
        """Extract selected document properties from preamble."""
        for node in [child for child in self.root.children if not child.species == 'document']:
            if node.species == 'title' and 'title' in node.args:
                self.preamble.__setitem__('title', node.args['title'])
            if node.species == 'author' and 'names' in node.args:
                self.preamble.__setitem__('author', node.args['names'])
            if node.species == 'date' and 'date' in node.args:
                self.preamble.__setitem__('date', node.args['date'])
            if node.species == 'documentclass' and 'name' in node.args:
                self.preamble.__setitem__('documentclass', node.args['name'])
            if node.species == 'graphicspath' and 'paths' in node.args:
                graphicspath = node.args['paths']
                self.preamble.__setitem__('graphicspath', graphicspath)

    def pp_labels(self):
        """Create a map of labels to the labelled Node objects."""
        self.labels = {}
        for node in self.get_phenotypes('label'):
            key = node.args['key'].chars(nobrackets=True)
            while node.parent:
                if hasattr(node, 'number'):
                    break
                if node.species in self.registry.block_commands:
                    break
                # if node.family == 'Environment':
                #     break
                node = node.parent
            self.labels.__setitem__(key, node)
        for node in self.get_phenotypes('bibitem'):
            key = node.args['key'].chars(nobrackets=True)
            self.labels.__setitem__(key, node)

    def pp_image_files(self):
        r"""Create a map of `includegraphics' objects onto file names.

        The filenames are relative to LATEX_ROOT and possibly `graphicspath'
        We need to check \graphicspath and \DeclareGraphicsExtensions
        The `graphics' table is used by write functions to
            (1) copy image files (static files) to the server 
            (2) include <img src="{{ ... }}"> elements in templates.

        """
        self.image_files = {}
        for node in self.get_phenotypes('includegraphics'):
            fname_str = node.args['file'].children[0].content
            self.image_files.__setitem__(node, fname_str)

        self.video_urls = {}
        for video in self.get_phenotypes('includevideo'):
            print(video.args)
            url_str = video.args['arg1'].chars(
                nobrackets=True)  # defined with \newfloat
            self.video_urls.__setitem__(video, url_str)

    def pp_widths(self):
        """Set width attributes for minipages and images"""
        for minipage in self.get_phenotypes('minipage'):
            width = minipage.args['width'].chars(
                nobrackets=True)  # mandatory arg
            minipage.width = parse_length(width)

        for image in self.get_phenotypes('includegraphics'):
            if 'options' in image.args:  # optional arg
                opt_arg_str = image.args['options'].chars(nobrackets=True)
                kw = parse_kv_opt_args(opt_arg_str)[1]
                if 'scale' in kw:
                    image.width = str(int(99*float(kw['scale']))) + '%'
                elif 'width' in kw:
                    image.width = parse_length(kw['width']) + '%'

    def pp_toc(self):
        """Experimental: create table of contents as a dict"""
        # recursive function (local)
        def _pp_toc(node):

            # check node is not 'None' (e.g. from optional arguments)
            if not node:
                return {}

            # hack for input or include (file contents parsed into children)
            if node.genus == 'Input':
                tt = {}
                for child in node.children:
                    tt.update(_pp_toc(child))
                return tt

            # check children for subsections etc.
            subs = []
            for child in node.children:
                s = _pp_toc(child)
                if s:
                    subs.append(s)

            # check node
            # hack: include root.document node to start things off
            if node.genus == 'Section' or node.species == 'document':
                return {node: subs}
            else:
                return {}

        # call recursive function on self.document (if it exists)
        self.toc = None
        if self.doc_root:
            self.toc = _pp_toc(self.doc_root)

    # search functions

    def get_container(self, node):
        """Get the nearest container for the node in the hierarchy, 
        i.e. the containing environment or other numbered species."""
        cont = node
        while cont.parent:
            if cont.family == 'Environment':
                return cont
            if cont.species in self.registry.numbered:
                return cont
            cont = cont.parent
        return None

    def get_phenotypes(self, species):
        """Retrieve all nodes of the given species."""

        # define inner recursive function
        def _get_phenotypes(node, species):

            # check node is not 'None' (e.g. from optional arguments)
            if not node:
                return []

            # init phenotype list
            phenotypes = []

            # check node
            if node.species == species:
                phenotypes.append(node)

            # check arguments (if any)
            if hasattr(node, 'args'):
                for arg in node.args.values():
                    phenotypes.extend(_get_phenotypes(arg, species))

            # check children
            for child in node.children:
                phenotypes.extend(_get_phenotypes(child, species))

            # return phenotypes
            return phenotypes

        # 2. call recursive function on root
        return _get_phenotypes(self.root, species)

    # write functions

    def write_chars(self):
        """Write tree as Latex source."""
        return self.root.chars()

    def write_xml(self):
        """Write tree in XML format."""
        return self.root.xml_print()

    def write_pretty(self):
        """Write in native LatexTree format (verbose)."""
        return self.root.pretty_print()

    def write_bbq(self, include_mathjax_header=False):
        """Extract MC/MA questions and typeset for Blackboard."""

        # init question pool
        pool = []

        # extract `questions` environments
        question_sets = self.get_phenotypes('questions')
        if not question_sets:
            return ''.join(pool)

        # iterate over question sets
        for question_set in question_sets:

            # iterate over questions
            for question in question_set.children:
                # ignore non-question objects (e.g. initial spaces encoded as Text nodes)
                # The parser put everything between \begin{itemize} and the first \item
                # command into a Text node. For valid Latex there should be only one of
                # these Text nodes, consisting only of whitespace (inc newlines).
                # TODO: Why do we not just test question.species == 'question'?
                if not question.genus == 'Item':
                    continue

                # find and extract choices environment (if any)
                choices_block = next((child for child in question.children if child.species in [
                                     'choices', 'checkboxes']), None)

                # bail out if no choices environment (MC or MA only)
                # TODO: true or false, fill the blank, ...
                #   TF TABquestion text TABtrue or false
                #   FIL TABquestion text
                #   FIB TABquestion text TABanswer text TABanswer text ... (max 100)
                if not choices_block:
                    continue

                # record question type (MC or MA)
                output = []
                if choices_block.species == 'choices':
                    output.append('MC')
                elif choices_block.species == 'checkboxes':
                    output.append('MA')
                else:
                    continue

                # init question text
                qu_text = ''
                if include_mathjax_header:
                    qu_text += '<script type="text/javascript" src="%s"/>' % mathjax_source

                # iterate over children
                # bbq format does not allow for content after the choices block
                # so everything after the question block is ignored
                for child in question.children:

                    # parse question text
                    if not child == choices_block:
                        qu_text += child.chars(non_breaking_spaces=True).rstrip('\n')

                    # process choices block (break on completion)
                    else:

                        # append question text to output list
                        output.append(qu_text.strip())

                        # iterate over choices
                        # as above we skip any leading whitespace (before to the first item)
                        for choice in child.children:
                            if not choice.genus == 'Item':
                                continue

                            # extract option and append to output list
                            option = ''.join(
                                [cc.chars(non_breaking_spaces=True) for cc in choice.children]).strip()
                            output.append(option)

                            # append 'correct' or 'incorrect' to the output list
                            status = 'CORRECT' if choice.species == 'correctchoice' else 'INCORRECT'
                            output.append(status)

                        # bbq format does not allow for content after the choices block
                        break

                # append to question pool
                print(output)
                pool.append('\t'.join(output))

            # hack to ignore multiple question sets
            break

            # end: iterate over questions
        # end: iterate over question sets
        return '\n'.join(pool)
