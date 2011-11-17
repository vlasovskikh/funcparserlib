# -*- coding: utf-8 -*-

import re
from nose.tools import eq_, ok_
from funcparserlib.lexer import make_tokenizer, LexerError, Token
from funcparserlib.parser import a, many, some, skip, finished, NoParseError

# Issue 31
def test_many_backtracking():
    x = a('x')
    y = a('y')
    expr = many(x + y) + x + x
    eq_(expr.parse('xyxyxx'), ([('x', 'y'), ('x', 'y')], 'x', 'x'))

# Issue 14
def test_error_info():
    tokenize = make_tokenizer([
        ('keyword', (r'(is|end)',)),
        ('id',      (r'[a-z]+',)),
        ('space',   (r'[ \t]+',)),
        ('nl',      (r'[\n\r]+',)),
    ])
    try:
        list(tokenize(u'f is ф'))
    except LexerError, e:
        eq_(unicode(e), u'cannot tokenize data: 1,6: "f is \u0444"')
    else:
        ok_(False, 'must raise LexerError')

    sometok = lambda type: some(lambda t: t.type == type)
    keyword = lambda s: a(Token('keyword', s))

    id = sometok('id')
    is_ = keyword('is')
    end = keyword('end')
    nl = sometok('nl')

    equality = id + skip(is_) + id >> tuple
    expr = equality + skip(nl)
    file = many(expr) + end

    msg = """\
spam is eggs
eggs isnt spam
end"""
    toks = [x for x in tokenize(msg) if x.type != 'space']
    try:
        file.parse(toks)
    except NoParseError, e:
        eq_(e.msg, u"got unexpected token: 2,11-2,14: id 'spam'")
        eq_(e.state.pos, 4)
        eq_(e.state.max, 7)
        # May raise KeyError
        t = toks[e.state.max]
        eq_(t, Token('id', 'spam'))
        eq_((t.start, t.end), ((2, 11), (2, 14)))
    else:
        ok_(False, 'must raise NoParseError')

