# bibliography.py
r'''
Defines the BibItem() and Bibliography() classes (both sub-classed from Node)

The Bibliography() object is initialized directly from 
a .bib file using the `bibtexparser` package.

We use registry.ClassFactory for unlisted fields
'''

import os
import logging
log = logging.getLogger(__name__)

import re, bibtexparser

from .registry import ClassFactory
from .command import Command
from .content import Text

class BibItem(Command):

    def __init__(self, citation_key=None):
        Command.__init__(self)
        self.citation_key = citation_key

    def __repr__(self):
        if self.citation_key:
            return '{}:{}({})'.format(self.genus, self.species, self.citation_key)
        return '{}:{}()'.format(self.genus, self.species)

    def harvard_dict(self):
        '''
        Create a dictionary of fields required for harvard-style citations.
        Returns a dict of citation keys mapped onto bibliographic information in the correct format.
        The main difficulty is with the 'author' key.
        '''
        bibtex_tags = ('title', 'author', 'year', 'publisher', 'isbn')
        harv = dict()
        surnames = list()
        initials = list()
        
        for child in self.children:

            # deal with author field
            if child.species == 'author':

                # split on 
                #   (1) authors: delimited by a comma (,) or an 'and', then
                #   (2) names: delimited by a point (.) or a space
                author_str = child.content                
                author_list = [x.split(' ') for x in re.split(',|and', author_str)]
                author_list = [[x.strip() for x in au if x] for au in author_list]
                for author in author_list:
                    surnames.append(author[-1])
                    initials.append('.'.join([x[0] for x in author[:-1]]) + '.')
                names = ['%s, %s' % name for name in zip(surnames, initials)]
                harv['author'] = ' and '.join([', '.join(names[:-1]), names[-1]])

            # copy bibtex (tag, content) pairs for tags in bibtex_fields
            else:
                if child.species in bibtex_tags:
                    harv[child.species] = child.content

        # set citation text e.g. (Evans 2012)
        if len(surnames) == 1:
            harv['citation'] = '(%s, %s)' % (surnames[0], harv['year'])
        elif len(surnames) == 2:
            harv['citation'] = '(%s & %s, %s)' % (surnames[0], surnames[1], harv['year'])
        elif len(surnames) > 3:
            harv['citation'] = '(%s et al. %s)' % (surnames[0], harv['year'])

        return harv

    
    def harvard(self):
        ''' print harvard-style item (should be done in a template!) '''
        title = ''
        author = ''
        year = ''
        publisher = ''
        for child in self.children:
            if child.species == 'title':
                title = child.content
            elif child.species == 'author':
                author_str = child.content
                auth_list = [x.split('.') for x in re.split(',|and', author_str)]
                auth_list = [[x.strip() for x in au] for au in auth_list]
                auth_parts = []
                for auth in auth_list:
                    name = auth[-1] + ' ' + '.'.join([x[0] for x in auth[:-1]]) + '.'
                    auth_parts.append(name)
                author = ' and '.join([', '.join(auth_parts[:-1]), auth_parts[-1]])
            elif child.species == 'year':
                year = child.content
            elif child.species == 'publisher':
                publisher = child.content
            else:
                pass
        return '%s (%s) %s. %s.' % (author, year, title, publisher)


class Bibliography(Command):
    r'''
    Bibliography is block command, whose `children` is a list of BibItem objects.
    This is an example of a Command whicl logically encloses what follows. 
    The data is read from a .bib file then parsed into a dictionary by the 
    `bibtexparser` package.
    At the moment it can only pull contents from a single bib file whereas
    the command allows for \bibliography{refs1.bib, refs2.bib} etc.
    '''
    
    def __init__(self, bibtex_filename=None, LATEX_ROOT=None):
        Command.__init__(self)
        self.filename = bibtex_filename
        if bibtex_filename:
            if LATEX_ROOT:
                bibtex_filename = os.path.join(LATEX_ROOT, bibtex_filename)
            self.read_bibtex_file(bibtex_filename)
        
    def read_bibtex_file(self, bibtex_filename):
        if not bibtex_filename[-4:] == '.bib':
            bibtex_filename = bibtex_filename + '.bib'
        try:
            with open(bibtex_filename) as bibtex_file:
                chars = bibtex_file.read()
        
        except FileNotFoundError as e:
            raise Exception('Bibtex file \'{}\' not found'.format(e.filename))

        # call bibtexparser
        bibtex_db = bibtexparser.loads(chars)
        for entry in bibtex_db.entries:
            bibitem = BibItem()
            for key, val in entry.items():
                if key == 'ID':
                    bibitem.citation_key = val
                else:
                    node = ClassFactory(str(key), [], BaseClass=Text)()
                    node.content = val
                    bibitem.append_child(node)
            self.append_child(bibitem)   
    
    def chars(self):
        ''' 
        The raw format is the original command "\bibliography{refs.bib}" 
        We are not testing bibtexparser!
        '''
        return r'\bibliography{{{}}}{}'.format(self.filename, self.post_space)
    
    def add_item(self, bibitem):
        if not isinstance(bibitem, BibItem):
            Exception('Bibliography objects can only contain BibItem objects')
            self.children.append(bibitem)
        
    def harvard(self):
        ''' string harvard entries together '''
        return '\n'.join([x.harvard() for x in self.children])


def test_bibtex():
    bibtex_filename = './test_docs/test_article/references.bib'
    bib = Bibliography(bibtex_filename)
    print(bib.pretty_print())
    print(bib.harvard())
    print(bib.chars())

if __name__ == '__main__':
    test_bibtex()
