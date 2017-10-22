# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import unittest
import six
from funcparserlib.lexer import make_tokenizer, LexerError, Token
from funcparserlib.parser import a, many, some, skip, NoParseError, oneplus


class ParsingTest(unittest.TestCase):
    def test_oneplus(self):
        x = a('x')
        y = a('y')
        expr = oneplus(x + y)
        self.assertEqual(expr.parse('xyxyxy'),
                         ([('x', 'y'), ('x', 'y'), ('x', 'y')]))

    # Issue 31
    def test_many_backtracking(self):
        x = a('x')
        y = a('y')
        expr = many(x + y) + x + x
        self.assertEqual(expr.parse('xyxyxx'),
                         ([('x', 'y'), ('x', 'y')], 'x', 'x'))

    # Issue 14
    def test_error_info(self):
        tokenize = make_tokenizer([
            ('keyword', (r'(is|end)',)),
            ('id', (r'[a-z]+',)),
            ('space', (r'[ \t]+',)),
            ('nl', (r'[\n\r]+',)),
        ])
        try:
            list(tokenize('f is ф'))
        except LexerError as e:
            self.assertEqual(six.text_type(e),
                             'cannot tokenize data: 1,6: "f is \u0444"')
        else:
            self.fail('must raise LexerError')

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
        except NoParseError as e:
            self.assertEqual(e.msg,
                             "got unexpected token: 2,11-2,14: id 'spam'")
            self.assertEqual(e.state.pos, 4)
            self.assertEqual(e.state.max, 7)
            # May raise KeyError
            t = toks[e.state.max]
            self.assertEqual(t, Token('id', 'spam'))
            self.assertEqual((t.start, t.end), ((2, 11), (2, 14)))
        else:
            self.fail('must raise NoParseError')
