# -*- coding: utf-8 -*-

import unittest
from funcparserlib.lexer import make_tokenizer, LexerError, Token
from funcparserlib.parser import a, many, some, skip, NoParseError


class ParsingTest(unittest.TestCase):
    # Issue 31
    def test_many_backtracking(self):
        x = a(u'x')
        y = a(u'y')
        expr = many(x + y) + x + x
        self.assertEqual(expr.parse(u'xyxyxx'),
                         ([(u'x', u'y'), (u'x', u'y')], u'x', u'x'))

    # Issue 14
    def test_error_info(self):
        tokenize = make_tokenizer([
            (u'keyword', (ur'(is|end)',)),
            (u'id', (ur'[a-z]+',)),
            (u'space', (ur'[ \t]+',)),
            (u'nl', (ur'[\n\r]+',)),
        ])
        try:
            list(tokenize(u'f is ф'))
        except LexerError, e:
            self.assertEqual(unicode(e),
                             u'cannot tokenize data: 1,6: "f is \u0444"')
        else:
            self.fail(u'must raise LexerError')

        sometok = lambda type: some(lambda t: t.type == type)
        keyword = lambda s: a(Token(u'keyword', s))

        id = sometok(u'id')
        is_ = keyword(u'is')
        end = keyword(u'end')
        nl = sometok(u'nl')

        equality = id + skip(is_) + id >> tuple
        expr = equality + skip(nl)
        file = many(expr) + end

        msg = """\
spam is eggs
eggs isnt spam
end"""
        toks = [x for x in tokenize(msg) if x.type != u'space']
        try:
            file.parse(toks)
        except NoParseError, e:
            self.assertEqual(e.msg,
                             u"got unexpected token: 2,11-2,14: id 'spam'")
            self.assertEqual(e.state.pos, 4)
            self.assertEqual(e.state.max, 7)
            # May raise KeyError
            t = toks[e.state.max]
            self.assertEqual(t, Token(u'id', u'spam'))
            self.assertEqual((t.start, t.end), ((2, 11), (2, 14)))
        else:
            self.fail(u'must raise NoParseError')
