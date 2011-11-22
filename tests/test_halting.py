# -*- coding: utf-8 -*-

'Tests for issue #8: prevent definitions of non-halting parsers.'

from funcparserlib.parser import (
        a, many, fwd, maybe, pure, oneplus, GrammarError, makes_progress,
        non_halting)
from funcparserlib.contrib.common import const
from nose.tools import ok_, assert_raises

x = a('x')
p1 = maybe(x)
p3 = maybe(x) + x
p4 = many(p3)
p5 = x | many(x)
p8 = x >> const(True)
p9 = pure(True)

def test_makes_progress():
    ok_(not makes_progress(p1))
    ok_(not makes_progress(p4))
    ok_(not makes_progress(p5))
    ok_(not makes_progress(p9))
    ok_(makes_progress(p3))
    ok_(makes_progress(p8))

def test_non_halting_many():
    assert_raises(GrammarError, lambda: many(many(x)).parse(''))
    assert_raises(GrammarError, lambda: oneplus(many(x)).parse(''))
    assert_raises(GrammarError, lambda: many(p1).parse(''))
    assert_raises(GrammarError, lambda: many(p5).parse(''))
    assert_raises(GrammarError, lambda: (x + many(p4)).parse(''))

def test_non_halting_left_recursive():
    h1 = fwd()
    h1.define(x + h1)
    ok_(not non_halting(h1))

    h2 = fwd()
    h2.define(x + (h2 | x))
    ok_(not non_halting(h2))

    nh1 = fwd()
    nh1.define(nh1 + x)
    ok_(non_halting(nh1))

    nh2 = fwd()
    nh2.define(x | nh2)
    ok_(non_halting(nh2))

    nh3_fwd = fwd()
    nh3_fwd.define(nh3_fwd)
    nh3 = x + nh3_fwd + x
    ok_(non_halting(nh3))

    nh4 = fwd()
    nh4.define(maybe(x) + nh4 + x)
    ok_(non_halting(nh4))

    nh5 = fwd()
    nh5.define(many(x) + maybe(x) + nh5 + x)
    ok_(non_halting(nh5))

    h3 = fwd()
    h3.define(maybe(x) + many(x) + x + h3)
    ok_(not non_halting(h3))

def test_halting():
    many(oneplus(x)).parse('x')
    many(p9 + x).parse('x')

