# vertical.py
r'''
Vertical boxes and spacing.

The following are defined in `coredefs.py`:
    vspace: 'par', 'smallskip', 'bigskip', ...

The parser uses Break() as abstract superclasses for bigskip, etc.
'''

from .command import Command
from .group import Group

class Vbox(Group):
    r''' Generic class for vertical boxes. '''
    def __init__(self):
        Group.__init__(self)


class Break(Command):
    r''' Generic class for vertical spacing and breaks. '''
    def __init__(self):
        Command.__init__(self)


class ParagraphBreak(Break):
    r''' Paragraph break. '''
    def __init__(self, blank_line=''):
        Break.__init__(self)
        self.blank_line = blank_line

    def __repr__(self):
        # return '{}:{}:{}({})'.format(self.family, self.genus, self.species, self.blank_line)
        return '{}:{}({})'.format(self.genus, self.species, self.blank_line)

    def chars(self):
        return('\n{}\n'.format(self.blank_line))
