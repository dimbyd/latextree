from latextree.parser.parser import Parser
from latextree import settings
import os
import pytest

defs_file = os.path.join(settings.EXTENSIONS_ROOT, 'examdef.json')

test_strings = [
        r'{pre \bi both \en english \cy cymraeg \bi post}',
        r'pre \en Hello world! \cy Hel\^{o} byd! \bi post',
]

@pytest.mark.parametrize("test_input", test_strings)
def test_parser(test_input):
    p = Parser()
    p.read_defs_file(defs_file)
    root = p.parse(test_input)
    assert test_input == root.chars()
