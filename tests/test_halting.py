# -*- coding: utf-8 -*-

'Tests for issue #8: prevent definitions of non-halting parsers.'

from funcparserlib.parser import a, many, maybe, pure, oneplus, GrammarError
from funcparserlib.contrib.common import const
from nose.tools import ok_, assert_raises

x = a('x')
p1 = maybe(x)
p3 = maybe(x) + x
p4 = many(p3)
p5 = x | many(x)
p8 = x >> const(True)
p9 = pure(True)

def test_always_succeeds():
    ok_(p1.always_succeeds)
    ok_(p4.always_succeeds)
    ok_(p5.always_succeeds)
    ok_(p9.always_succeeds)
    ok_(not p3.always_succeeds)
    ok_(not p8.always_succeeds)

def test_non_halting():
    assert_raises(GrammarError, lambda: many(many(x)))
    assert_raises(GrammarError, lambda: oneplus(many(x)))
    assert_raises(GrammarError, lambda: many(p1))
    assert_raises(GrammarError, lambda: many(p5))
    assert_raises(GrammarError, lambda: x + many(p4))

def test_halting():
    many(oneplus(x))
    many(p9 + x)

