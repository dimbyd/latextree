# test_node.py

from latextree.parser.command import Command, Environment
from latextree.parser.content import Text

def test_initial_children():
    node = Command()
    assert len(node.children)== 0

def test_species():
    node = Text()
    assert node.species == 'Text'

def test_add_child():
    node = Environment()
    child = Text('abcde')
    node.append_child(child)
    assert node.children[-1] == child
