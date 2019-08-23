# horizontal.py
r'''
Horizontal spacing and boxes.

The following are defined in `coredefs.py`:
    hspace: 'quad', 'qquad', 'indent', ...
The registry builds Space() as abstract superclasses for these.
'''

from .command import Command
from .group import Group

class Mbox(Group):
    r''' Generic class for horizontal boxes'''
    def __init__(self):
        Group.__init__(self)

class Space(Command):
    r''' Generic class for horizontal spaces'''
    def __init__(self):
        Command.__init__(self)
