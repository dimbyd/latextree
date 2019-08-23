# test_token.py
from latextree.parser.tokens import Token, TokenStream

def test_types():
    t = Token(0,'cmd')
    assert isinstance(t.catcode, int) and isinstance(t.value, str)

def test_equality():
    t1 = Token(0,'cmd')
    t2 = Token(0,'cmd')
    assert t1 == t2

def test_stream_equality():
    ts1 = TokenStream(r'\test{123}')
    ts2 = TokenStream(r'\test{123}')
    assert ts1 == ts2
