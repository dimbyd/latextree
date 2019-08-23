# test_token.py
from latextree.parser.command import Command
from latextree.parser.registry import ClassFactory, Registry

def test_registry():

    c = ClassFactory('textbf', ['contents'], BaseClass=Command)
    o = c(contents='bingo')
    print(o)
    print(o.__dict__)

    c2 = ClassFactory('$', [], BaseClass=Command)
    o2 = c2()
    print(o2)
    print(o2.__dict__)

    b4 = ClassFactory('TestClass', [], BaseClass=Command)
    c4 = ClassFactory('&', [], BaseClass=b4)
    print(c4)
    o4 = c4()
    print(o4)
    print(o4.__dict__)

