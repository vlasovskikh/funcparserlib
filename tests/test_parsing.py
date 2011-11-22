# -*- coding: utf-8 -*-

import re
from nose.tools import eq_, ok_
from funcparserlib.lexer import make_tokenizer, Spec, LexerError, Token
from funcparserlib.parser import a, many, tok, skip, eof, ParserError

# Issue 31
def test_many_backtracking():
    x = a('x')
    y = a('y')
    expr = many(x + y) + x + x
    eq_(expr.parse('xyxyxx'), ([('x', 'y'), ('x', 'y')], 'x', 'x'))

# Issue 14
def test_error_info():
    tokenize = make_tokenizer([
        Spec('keyword', r'(is|end)'),
        Spec('id',      r'[a-z]+'),
        Spec('space',   r'[ \t]+'),
        Spec('nl',      r'[\n\r]+'),
    ])
    try:
        list(tokenize(u'f is ф'))
    except LexerError, e:
        eq_(unicode(e), u'1,6-1,6: cannot tokenize data: "f is \u0444"')
    else:
        ok_(False, 'must raise LexerError')

    keyword = lambda s: tok('keyword', s)

    id = tok('id')
    is_ = keyword('is')
    end = keyword('end')
    nl = tok('nl')

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
    except ParserError, e:
        msg, pos, i = e.args
        eq_(msg, u"got unexpected token: id 'spam'")
        eq_(pos, ((2, 11), (2, 14)))
        # May raise KeyError
        t = toks[i]
        eq_(t, Token('id', 'spam'))
    else:
        ok_(False, 'must raise ParserError')

