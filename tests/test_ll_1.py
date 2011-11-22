# -*- coding: utf-8 -*-

from funcparserlib.parser import (a, maybe, many, pure, fwd, first, _EPSYLON)
from funcparserlib.lexer import Token
from nose.tools import eq_, ok_, assert_raises

def test_first_non_pure():
    eq_(first(a('x')), ['x'])
    eq_(first(a('x') + a('y')), ['x'])
    eq_(first(a('x') | a('y')), ['x', 'y'])

def test_first_maybe():
    eq_(first(maybe(a('x'))), ['x', _EPSYLON])
    eq_(first(maybe(a('x')) + a('y')), ['x', 'y'])
    eq_(first(maybe(a('x')) + maybe(a('y'))), ['x', 'y', _EPSYLON])

    eq_(first(maybe(a('x')) | a('y')), ['x', _EPSYLON, 'y'])
    eq_(first(a('x') | maybe(a('y'))), ['x', 'y', _EPSYLON])
    eq_(first(maybe(a('x')) | maybe(a('y'))), ['x', _EPSYLON, 'y', _EPSYLON])

def test_first_many():
    eq_(first(many(a('x'))), ['x', _EPSYLON])
    eq_(first(many(a('x')) + a('y')), ['x', 'y'])
    eq_(first(a('x') + many(a('y'))), ['x'])

