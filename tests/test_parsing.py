# -*- coding: utf-8 -*-

import unittest
from typing import Optional, Tuple

from funcparserlib.lexer import TokenSpec, make_tokenizer, LexerError, Token
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
    some,
)


class ParsingTest(unittest.TestCase):
    def test_oneplus(self) -> None:
        x = a("x")
        y = a("y")
        expr = oneplus(x + y)
        # noinspection SpellCheckingInspection
        self.assertEqual(expr.parse("xyxyxy"), ([("x", "y"), ("x", "y"), ("x", "y")]))

    # Issue 31
    def test_many_backtracking(self) -> None:
        x = a("x")
        y = a("y")
        expr = many(x + y) + x + x
        # noinspection SpellCheckingInspection
        self.assertEqual(expr.parse("xyxyxx"), ([("x", "y"), ("x", "y")], "x", "x"))

    # Issue 14
    def test_error_info(self) -> None:
        tokenize = make_tokenizer(
            [
                TokenSpec("keyword", r"\b(is|end)\b"),
                TokenSpec("id", r"[a-z_]+"),
                ("space", (r"[ \t]+",)),  # Legacy token spec
                TokenSpec("nl", r"[\n\r]+"),
            ]
        )
        with self.assertRaises(LexerError) as ctx:
            list(tokenize("f is ф"))
        self.assertEqual(str(ctx.exception), 'cannot tokenize data: 1,6: "f is \u0444"')

        def make_equality(values: Tuple[str, str]) -> Tuple[str, str]:
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
        self.assertEqual(
            ctx2.exception.msg,
            "2,5-2,10: got unexpected token: 'is_not', expected: 'is'",
        )

    def test_ok_ignored(self) -> None:
        x = a("x")
        y = a("y")
        expr: Parser[str, str] = -x + y
        self.assertEqual(expr.parse("xy"), "y")

    def test_ignored_ok(self) -> None:
        x = a("x")
        y = a("y")
        expr: Parser[str, str] = x + -y
        self.assertEqual(expr.parse("xy"), "x")

    def test_ignored_ok_ok(self) -> None:
        x = a("x")
        y = a("y")
        expr: Parser[str, Tuple[str, str]] = -x + y + x
        self.assertEqual(expr.parse("xyx"), ("y", "x"))

    def test_ok_ignored_ok(self) -> None:
        x = a("x")
        y = a("y")
        expr: Parser[str, Tuple[str, str]] = x + -y + x
        self.assertEqual(expr.parse("xyx"), ("x", "x"))

    def test_ok_ok_ok(self) -> None:
        x = a("x")
        y = a("y")
        expr: Parser[str, Tuple[str, str]] = x + y + x
        self.assertEqual(expr.parse("xyx"), ("x", "y", "x"))

    def test_ok_ok_ignored(self) -> None:
        x = a("x")
        y = a("y")
        expr: Parser[str, Tuple[str, str]] = x + y + -x
        self.assertEqual(expr.parse("xyx"), ("x", "y"))

    def test_ignored_ignored_ok(self) -> None:
        x = a("x")
        y = a("y")
        expr: Parser[str, str] = -x + -x + y
        self.assertEqual(expr.parse("xxy"), "y")

    def test_ok_ignored_ignored(self) -> None:
        x = a("x")
        y = a("y")
        expr: Parser[str, str] = x + -y + -y
        self.assertEqual(expr.parse("xyy"), "x")

    def test_ignored_ignored(self) -> None:
        x = a("x")
        y = a("y")
        expr: Parser[str, _Ignored] = -x + -y
        self.assertEqual(expr.parse("xy"), _Ignored("y"))

    def test_ignored_ignored_ignored(self) -> None:
        x = a("x")
        y = a("y")
        z = a("z")
        expr: Parser[str, _Ignored] = -x + -y + -z
        self.assertEqual(expr.parse("xyz"), _Ignored("z"))

    def test_ignored_maybe(self) -> None:
        x = a("x")
        y = a("y")
        expr: Parser[str, str] = -maybe(x) + y
        self.assertEqual(expr.parse("xy"), "y")
        self.assertEqual(expr.parse("y"), "y")

    def test_maybe_ignored(self) -> None:
        x = a("x")
        y = a("y")
        expr: Parser[str, Tuple[Optional[_Ignored], str]] = maybe(-x) + y
        self.assertEqual(expr.parse("xy"), (_Ignored("x"), "y"))
        self.assertEqual(expr.parse("y"), (None, "y"))

    def test_ignored_maybe_ignored(self) -> None:
        x = a("x")
        y = a("y")
        expr: Parser[str, Optional[str]] = -x + maybe(y) + -x
        self.assertEqual(expr.parse("xyx"), "y")
        self.assertEqual(expr.parse("xx"), None)

    def test_compare_token_with_none(self) -> None:
        # https://github.com/vlasovskikh/funcparserlib/pull/58
        specs = [
            ("id", (r"\w+",)),
        ]
        tokenize = make_tokenizer(specs)
        tokens = list(tokenize("foo"))
        expr = maybe(a(None))
        self.assertEqual(expr.parse(tokens), None)  # type: ignore

    def test_seq_parse_error(self) -> None:
        expr = a("x") + a("y")
        with self.assertRaises(NoParseError) as ctx:
            expr.parse("xz")
        self.assertEqual(ctx.exception.msg, "got unexpected token: 'z', expected: 'y'")

    def test_alt_2_parse_error(self) -> None:
        expr = a("x") + (a("x") | a("y"))
        with self.assertRaises(NoParseError) as ctx:
            expr.parse("xz")
        self.assertEqual(
            ctx.exception.msg, "got unexpected token: 'z', expected: 'x' or 'y'"
        )

    def test_alt_3_parse_error(self) -> None:
        expr = a("x") + (a("x") | a("y") | a("z"))
        with self.assertRaises(NoParseError) as ctx:
            expr.parse("xa")
        self.assertEqual(
            ctx.exception.msg,
            "got unexpected token: 'a', expected: 'x' or 'y' or 'z'",
        )

    def test_alt_3_two_steps_parse_error(self) -> None:
        expr = a("x") + (a("x") | (a("y") + a("a")))
        with self.assertRaises(NoParseError) as ctx:
            expr.parse("xyz")
        self.assertEqual(ctx.exception.msg, "got unexpected token: 'z', expected: 'a'")

    def test_expected_eof_error(self) -> None:
        expr = a("x") + finished
        with self.assertRaises(NoParseError) as ctx:
            expr.parse("xy")
        self.assertEqual(
            ctx.exception.msg,
            "got unexpected token: 'y', expected: end of input",
        )

    def test_expected_second_in_sequence_error(self) -> None:
        expr = a("x") + a("y")
        with self.assertRaises(NoParseError) as ctx:
            expr.parse("xz")
        self.assertEqual(ctx.exception.msg, "got unexpected token: 'z', expected: 'y'")

    def test_forward_decl_nested_matching_error(self) -> None:
        expr = forward_decl()
        expr.define(a("x") + maybe(expr) + a("y"))
        with self.assertRaises(NoParseError) as ctx:
            expr.parse("xxy")
        self.assertEqual(
            ctx.exception.msg, "got unexpected end of input, expected: 'y'"
        )

    def test_expected_token_type_error(self) -> None:
        expr = tok("number")
        with self.assertRaises(NoParseError) as ctx:
            expr.parse([Token("id", "x")])
        self.assertEqual(
            ctx.exception.msg, "got unexpected token: 'x', expected: number"
        )

    def test_expected_exact_token_error(self) -> None:
        expr = tok("operator", "=")
        with self.assertRaises(NoParseError) as ctx:
            expr.parse([Token("operator", "+")])
        self.assertEqual(ctx.exception.msg, "got unexpected token: '+', expected: '='")

    def test_unexpected_eof(self) -> None:
        expr = (a("x") + a("y")) | a("z")
        with self.assertRaises(NoParseError) as ctx:
            expr.parse("x")
        self.assertEqual(
            ctx.exception.msg, "got unexpected end of input, expected: 'y'"
        )

    def test_expected_transform_parsing_results_error(self) -> None:
        expr = (a("1") >> int) | a("2")
        with self.assertRaises(NoParseError) as ctx:
            expr.parse("x")
        self.assertEqual(
            ctx.exception.msg, "got unexpected token: 'x', expected: '1' or '2'"
        )

    def test_expected_sequence_with_skipped_parts(self) -> None:
        expr = (-a("x") + a("y")) | a("z")
        with self.assertRaises(NoParseError) as ctx:
            expr.parse("b")
        self.assertEqual(
            ctx.exception.msg,
            "got unexpected token: 'b', expected: ('x', 'y') or 'z'",
        )

    def test_expected_some_without_name(self) -> None:
        def lowercase(t: str) -> bool:
            return t.islower()

        expr = some(lowercase)
        with self.assertRaises(NoParseError) as ctx:
            expr.parse("A")
        self.assertEqual(
            ctx.exception.msg, "got unexpected token: 'A', expected: some(...)"
        )

    def test_expected_forward_decl_without_name(self) -> None:
        nested = forward_decl()
        nested.define(-a("a") + maybe(nested) + -a("z"))
        expr = nested | a("x")
        with self.assertRaises(NoParseError) as ctx:
            expr.parse("y")
        self.assertEqual(
            ctx.exception.msg,
            "got unexpected token: 'y', "
            "expected: (('a', [ forward_decl() ]), 'z') or 'x'",
        )

    def test_expected_forward_decl_with_name(self) -> None:
        nested = forward_decl().named("nested")
        nested.define(-a("a") + maybe(nested) + -a("z"))
        expr = nested | a("x")
        with self.assertRaises(NoParseError) as ctx:
            expr.parse("y")
        self.assertEqual(
            ctx.exception.msg,
            "got unexpected token: 'y', expected: (('a', [ nested ]), 'z') or 'x'",
        )

    def test_end_of_input_after_many_alternatives(self) -> None:
        brackets = a("[") + a("]")
        expr = many(a("x") | brackets) + finished
        with self.assertRaises(NoParseError) as ctx:
            expr.parse("[")
        self.assertEqual(
            ctx.exception.msg, "got unexpected end of input, expected: ']'"
        )

    def test_parse_one_more_then_rollback_to_single(self) -> None:
        mul = a("x") + many(a("*") + a("y"))
        add = mul + many(a("+") + mul)
        expr = add + finished
        with self.assertRaises(NoParseError) as ctx:
            expr.parse("x*")
        self.assertEqual(
            ctx.exception.msg, "got unexpected end of input, expected: 'y'"
        )

    def test_parse_one_more_then_rollback_to_alternative(self) -> None:
        mul = a("x") + many(a("*") + a("y"))
        addsub = mul + many((a("+") | a("-")) + mul)
        expr = addsub + finished
        with self.assertRaises(NoParseError) as ctx:
            expr.parse("x*")
        self.assertEqual(
            ctx.exception.msg, "got unexpected end of input, expected: 'y'"
        )
