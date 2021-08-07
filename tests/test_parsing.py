# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import unittest
from typing import Text, Optional, Tuple

import six

from funcparserlib.lexer import make_tokenizer, LexerError, Token
from funcparserlib.parser import (
    a,
    many,
    NoParseError,
    oneplus,
    Parser,
    maybe,
    _Ignored,  # noqa
    tok,
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
                ("keyword", (r"\b(is|end)\b",)),
                ("id", (r"[a-z_]+",)),
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

        def make_equality(values):
            # type: (Tuple[str, str]) -> Tuple[str, str]
            v1, v2 = values
            return v1, v2

        tok_id = tok("id")
        equality = tok_id + -tok("keyword", "is") + tok_id >> make_equality
        expr = equality + -tok("nl")
        file = many(expr) + tok("keyword", "end")

        msg = """\
spam is eggs
foo is_not bar
end"""
        tokens = [x for x in tokenize(msg) if x.type != "space"]
        try:
            file.parse(tokens)
        except NoParseError as e:
            self.assertEqual(e.state.pos, 4)
            self.assertEqual(e.state.max, 5)
            # May raise KeyError
            t = tokens[e.state.max]
            self.assertEqual(t, Token("id", "is_not"))
            self.assertEqual((t.start, t.end), ((2, 5), (2, 10)))
            self.assertEqual("got unexpected token: 2,5-2,10: id 'is_not'", e.msg)
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
