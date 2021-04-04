# -*- coding: utf-8 -*-

# Copyright © 2009/2021 Andrey Vlasovskikh
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be included in all copies
# or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""A JSON parser using funcparserlib.

The parser is based on [the JSON grammar][1].

  [1]: https://tools.ietf.org/html/rfc4627
"""

from __future__ import print_function, unicode_literals

import logging
import os
import re
import sys
from pprint import pformat
from re import VERBOSE
from typing import (
    List,
    Sequence,
    Optional,
    Tuple,
    Any,
    Dict,
    Match,
    TypeVar,
    Callable,
    Text,
)

import six

from funcparserlib.lexer import make_tokenizer, Token, LexerError
from funcparserlib.parser import (
    some,
    a,
    maybe,
    many,
    finished,
    skip,
    forward_decl,
    NoParseError,
    Parser,
)

ENCODING = "UTF-8"
# noinspection SpellCheckingInspection
regexps = {
    "escaped": r"""
        \\                                  # Escape
          ((?P<standard>["\\/bfnrt])        # Standard escapes
        | (u(?P<unicode>[0-9A-Fa-f]{4})))   # uXXXX
        """,
    "unescaped": r"""
        [^"\\]                              # Unescaped: avoid ["\\]
        """,
}
re_esc = re.compile(regexps["escaped"], VERBOSE)
T = TypeVar("T")  # noqa


def tokenize(s):
    # type: (Text) -> List[Token]
    specs = [
        ("Space", (r"[ \t\r\n]+",)),
        ("String", (r'"(%(unescaped)s | %(escaped)s)*"' % regexps, VERBOSE)),
        (
            "Number",
            (
                r"""
                -?                  # Minus
                (0|([1-9][0-9]*))   # Int
                (\.[0-9]+)?         # Frac
                ([Ee][+-][0-9]+)?   # Exp
            """,
                VERBOSE,
            ),
        ),
        ("Op", (r"[{}\[\]\-,:]",)),
        ("Name", (r"[A-Za-z_][A-Za-z_0-9]*",)),
    ]
    useless = ["Space"]
    t = make_tokenizer(specs)
    return [x for x in t(s) if x.type not in useless]


def parse(tokens):
    # type: (Sequence[Token]) -> object

    def const(x):
        # type: (T) -> Callable[[Any], T]
        return lambda _: x

    def tok_val(t):
        # type: (Token) -> Text
        return t.value

    def tok_type(name):
        # type: (Text) -> Parser[Token, Text]
        def is_type(t):
            # type: (Token) -> bool
            return t.type == name

        return some(is_type) >> tok_val

    def op(s):
        # type: (Text) -> Parser[Token, Text]
        return a(Token("Op", s)) >> tok_val

    def op_(s):
        # type: (Text) -> Parser[Token, Text]
        return skip(op(s))

    def n(s):
        # type: (Text) -> Parser[Token, Text]
        return a(Token("Name", s)) >> tok_val

    def make_array(values):
        # type: (Optional[Tuple[object, List[object]]]) -> List[Any]
        if values is None:
            return []
        else:
            return [values[0]] + values[1]

    def make_object(values):
        # type: (Optional[Tuple[object, List[object]]]) -> Dict[Any, Any]
        return dict(make_array(values))

    def make_number(s):
        # type: (Text) -> float
        try:
            return int(s)
        except ValueError:
            return float(s)

    def unescape(s):
        # type: (Text) -> Text
        std = {
            '"': '"',
            "\\": "\\",
            "/": "/",
            "b": "\b",
            "f": "\f",
            "n": "\n",
            "r": "\r",
            "t": "\t",
        }

        def sub(m):
            # type: (Match[Text]) -> Text
            if m.group("standard") is not None:  # noqa
                return std[m.group("standard")]  # noqa
            else:
                return six.unichr(int(m.group("unicode"), 16))  # noqa

        return re_esc.sub(sub, s)

    def make_string(s):
        # type: (Text) -> Text
        return unescape(s[1:-1])

    null = n("null") >> const(None)
    true = n("true") >> const(True)
    false = n("false") >> const(False)
    number = tok_type("Number") >> make_number
    string = tok_type("String") >> make_string
    value = forward_decl()
    member = string + op_(":") + value >> tuple
    json_object = (
        op_("{") + maybe(member + many(op_(",") + member)) + op_("}") >> make_object
    )
    json_array = (
        op_("[") + maybe(value + many(op_(",") + value)) + op_("]") >> make_array
    )
    value.define(null | true | false | json_object | json_array | number | string)
    json_text = json_object | json_array
    json_file = json_text + skip(finished)

    return json_file.parse(tokens)


def loads(s):
    # type: (Text) -> Any
    return parse(tokenize(s))


def main():
    # type: () -> None
    logging.basicConfig(level=logging.DEBUG)
    try:
        stdin = os.fdopen(sys.stdin.fileno(), "rb")
        text = stdin.read().decode(ENCODING)
        tree = loads(text)
        print(pformat(tree))
    except (NoParseError, LexerError) as e:
        msg = ("syntax error: %s" % e).encode(ENCODING)
        print(msg, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
