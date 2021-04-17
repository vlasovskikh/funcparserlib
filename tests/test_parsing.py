# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import unittest
from typing import Text, Optional, Tuple

import six

from funcparserlib.lexer import make_tokenizer, LexerError, Token
from funcparserlib.parser import (
    a,
    many,
    some,
    skip,
    NoParseError,
    oneplus,
    Parser,
    maybe,
    _Ignored,  # noqa
)


class ParsingTest(unittest.TestCase):
    def test_oneplus(self):
        # type: () -> None
        x = a("x")
        y = a("y")
        expr = oneplus(x + y)
        # noinspection SpellCheckingInspection
        self.assertEqual(expr.parse("xyxyxy"), ([("x", "y"), ("x", "y"), ("x", "y")]))

    # Issue 31
    def test_many_backtracking(self):
        # type: () -> None
        x = a("x")
        y = a("y")
        expr = many(x + y) + x + x
        # noinspection SpellCheckingInspection
        self.assertEqual(expr.parse("xyxyxx"), ([("x", "y"), ("x", "y")], "x", "x"))

    # Issue 14
    def test_error_info(self):
        # type: () -> None
        tokenize = make_tokenizer(
            [
                ("keyword", (r"(is|end)",)),
                ("id", (r"[a-z]+",)),
                ("space", (r"[ \t]+",)),
                ("nl", (r"[\n\r]+",)),
            ]
        )
        try:
            list(tokenize("f is ф"))
        except LexerError as e:
            self.assertEqual(
                six.text_type(e), 'cannot tokenize data: 1,6: "f is \u0444"'
            )
        else:
            self.fail("must raise LexerError")

        def some_tok(type_name):
            # type: (Text) -> Parser[Token, Token]
            def is_type(token):
                # type: (Token) -> bool
                return token.type == type_name

            return some(is_type)

        def keyword(s):
            # type: (Text) -> Parser[Token, Token]
            return a(Token("keyword", s))

        def make_equality(values):
            # type: (Tuple[Token, Token]) -> Tuple[Token, Token]
            v1, v2 = values
            return v1, v2

        tok_id = some_tok("id")
        is_ = keyword("is")
        end = keyword("end")
        nl = some_tok("nl")

        equality = tok_id + skip(is_) + tok_id >> make_equality
        expr = equality + skip(nl)
        file = many(expr) + end

        # noinspection GrazieInspection,SpellCheckingInspection
        msg = """\
spam is eggs
eggs isnt spam
end"""
        tokens = [x for x in tokenize(msg) if x.type != "space"]
        try:
            file.parse(tokens)
        except NoParseError as e:
            self.assertEqual(e.msg, "got unexpected token: 2,11-2,14: id 'spam'")
            self.assertEqual(e.state.pos, 4)
            self.assertEqual(e.state.max, 7)
            # May raise KeyError
            t = tokens[e.state.max]
            self.assertEqual(t, Token("id", "spam"))
            self.assertEqual((t.start, t.end), ((2, 11), (2, 14)))
        else:
            self.fail("must raise NoParseError")

    def test_ok_ignored(self):
        # type: () -> None
        x = a("x")
        y = a("y")
        expr = -x + y  # type: Parser[Text, Text]
        self.assertEqual(expr.parse("xy"), "y")

    def test_ignored_ok(self):
        # type: () -> None
        x = a("x")
        y = a("y")
        expr = x + -y  # type: Parser[Text, Text]
        self.assertEqual(expr.parse("xy"), "x")

    def test_ignored_ok_ok(self):
        # type: () -> None
        x = a("x")
        y = a("y")
        expr = -x + y + x  # type: Parser[Text, Tuple[Text, Text]]
        self.assertEqual(expr.parse("xyx"), ("y", "x"))

    def test_ok_ignored_ok(self):
        # type: () -> None
        x = a("x")
        y = a("y")
        expr = x + -y + x  # type: Parser[Text, Tuple[Text, Text]]
        self.assertEqual(expr.parse("xyx"), ("x", "x"))

    def test_ok_ok_ok(self):
        # type: () -> None
        x = a("x")
        y = a("y")
        expr = x + y + x  # type: Parser[Text, Tuple[Text, Text, Text]]
        self.assertEqual(expr.parse("xyx"), ("x", "y", "x"))

    def test_ok_ok_ignored(self):
        # type: () -> None
        x = a("x")
        y = a("y")
        expr = x + y + -x  # type: Parser[Text, Tuple[Text, Text]]
        self.assertEqual(expr.parse("xyx"), ("x", "y"))

    def test_ignored_ignored_ok(self):
        # type: () -> None
        x = a("x")
        y = a("y")
        expr = -x + -x + y  # type: Parser[Text, Text]
        self.assertEqual(expr.parse("xxy"), "y")

    def test_ok_ignored_ignored(self):
        # type: () -> None
        x = a("x")
        y = a("y")
        expr = x + -y + -y  # type: Parser[Text, Text]
        self.assertEqual(expr.parse("xyy"), "x")

    def test_ignored_ignored(self):
        # type: () -> None
        x = a("x")
        y = a("y")
        expr = -x + -y  # type: Parser[Text, _Ignored]
        self.assertEqual(expr.parse("xy"), _Ignored("y"))

    def test_ignored_ignored_ignored(self):
        # type: () -> None
        x = a("x")
        y = a("y")
        z = a("z")
        expr = -x + -y + -z  # type: Parser[Text, _Ignored]
        self.assertEqual(expr.parse("xyz"), _Ignored("z"))

    def test_ignored_maybe(self):
        # type: () -> None
        x = a("x")
        y = a("y")
        expr = -maybe(x) + y  # type: Parser[Text, Text]
        self.assertEqual(expr.parse("xy"), "y")
        self.assertEqual(expr.parse("y"), "y")

    def test_maybe_ignored(self):
        # type: () -> None
        x = a("x")
        y = a("y")
        expr = maybe(-x) + y  # type: Parser[Text, Tuple[Optional[_Ignored], Text]]
        self.assertEqual(expr.parse("xy"), (_Ignored("x"), "y"))
        self.assertEqual(expr.parse("y"), (None, "y"))

    def test_ignored_maybe_ignored(self):
        # type: () -> None
        x = a("x")
        y = a("y")
        expr = -x + maybe(y) + -x  # type: Parser[Text, Optional[Text]]
        self.assertEqual(expr.parse("xyx"), "y")
        self.assertEqual(expr.parse("xx"), None)

    def test_compare_token_with_none(self):
        # type: () -> None
        # https://github.com/vlasovskikh/funcparserlib/pull/58
        specs = [
            ("id", (r"\w+",)),
        ]
        tokenize = make_tokenizer(specs)
        tokens = list(tokenize("foo"))
        expr = maybe(a(None))
        self.assertEqual(expr.parse(tokens), None)  # type: ignore
