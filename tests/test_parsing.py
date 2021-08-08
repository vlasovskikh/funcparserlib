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
    finished,
    forward_decl,
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
        with self.assertRaises(LexerError) as ctx:
            list(tokenize("f is ф"))
        self.assertEqual(
            six.text_type(ctx.exception), 'cannot tokenize data: 1,6: "f is \u0444"'
        )

        def make_equality(values):
            # type: (Tuple[Text, Text]) -> Tuple[Text, Text]
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
        with self.assertRaises(NoParseError) as ctx2:
            file.parse(tokens)
        self.assertEqual(ctx2.exception.state.pos, 4)
        self.assertEqual(ctx2.exception.state.max, 5)
        # May raise KeyError
        t = tokens[ctx2.exception.state.max]
        self.assertEqual(t, Token("id", "is_not"))
        self.assertEqual((t.start, t.end), ((2, 5), (2, 10)))
        if six.PY2:
            # noinspection SpellCheckingInspection
            msg = "2,5-2,10: got unexpected token: u'is_not', expected: u'is'"
        else:
            msg = "2,5-2,10: got unexpected token: 'is_not', expected: 'is'"
        self.assertEqual(ctx2.exception.msg, msg)

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

    def test_seq_parse_error(self):
        # type: () -> None
        expr = a("x") + a("y")
        with self.assertRaises(NoParseError) as ctx:
            expr.parse("xz")
        if six.PY2:
            msg = "got unexpected token: u'z', expected: u'y'"
        else:
            msg = "got unexpected token: 'z', expected: 'y'"
        self.assertEqual(ctx.exception.msg, msg)

    def test_alt_2_parse_error(self):
        # type: () -> None
        expr = a("x") + (a("x") | a("y"))
        with self.assertRaises(NoParseError) as ctx:
            expr.parse("xz")
        if six.PY2:
            msg = "got unexpected token: u'z', expected: u'x' or u'y'"
        else:
            msg = "got unexpected token: 'z', expected: 'x' or 'y'"
        self.assertEqual(ctx.exception.msg, msg)

    def test_alt_3_parse_error(self):
        # type: () -> None
        expr = a("x") + (a("x") | a("y") | a("z"))
        with self.assertRaises(NoParseError) as ctx:
            expr.parse("xa")
        if six.PY2:
            msg = "got unexpected token: u'a', expected: u'x' or u'y' or u'z'"
        else:
            msg = "got unexpected token: 'a', expected: 'x' or 'y' or 'z'"
        self.assertEqual(ctx.exception.msg, msg)

    def test_alt_3_two_steps_parse_error(self):
        # type: () -> None
        expr = a("x") + (a("x") | (a("y") + a("a")))
        with self.assertRaises(NoParseError) as ctx:
            expr.parse("xyz")
        if six.PY2:
            msg = "got unexpected token: u'z', expected: u'a'"
        else:
            msg = "got unexpected token: 'z', expected: 'a'"
        self.assertEqual(ctx.exception.msg, msg)

    def test_expected_eof_error(self):
        # type: () -> None
        expr = a("x") + finished
        with self.assertRaises(NoParseError) as ctx:
            expr.parse("xy")
        if six.PY2:
            msg = "got unexpected token: u'y', expected: end of file"
        else:
            msg = "got unexpected token: 'y', expected: end of file"
        self.assertEqual(ctx.exception.msg, msg)

    def test_expected_second_in_sequence_error(self):
        # type: () -> None
        expr = a("x") + a("y")
        with self.assertRaises(NoParseError) as ctx:
            expr.parse("xz")
        if six.PY2:
            msg = "got unexpected token: u'z', expected: u'y'"
        else:
            msg = "got unexpected token: 'z', expected: 'y'"
        self.assertEqual(ctx.exception.msg, msg)

    def test_forward_decl_nested_matching_error(self):
        # type: () -> None
        expr = forward_decl()
        expr.define(a("x") + maybe(expr) + a("y"))
        with self.assertRaises(NoParseError) as ctx:
            expr.parse("xxy")
        if six.PY2:
            msg = "got unexpected end of file, expected: u'y'"
        else:
            msg = "got unexpected end of file, expected: 'y'"
        self.assertEqual(ctx.exception.msg, msg)

    def test_expected_token_type_error(self):
        # type: () -> None
        expr = tok("number")
        with self.assertRaises(NoParseError) as ctx:
            expr.parse([Token("id", "x")])
        if six.PY2:
            msg = "got unexpected token: u'x', expected: number"
        else:
            msg = "got unexpected token: 'x', expected: number"
        self.assertEqual(ctx.exception.msg, msg)

    def test_expected_exact_token_error(self):
        # type: () -> None
        expr = tok("operator", "=")
        with self.assertRaises(NoParseError) as ctx:
            expr.parse([Token("operator", "+")])
        if six.PY2:
            msg = "got unexpected token: u'+', expected: u'='"
        else:
            msg = "got unexpected token: '+', expected: '='"
        self.assertEqual(ctx.exception.msg, msg)
