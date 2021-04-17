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

from __future__ import unicode_literals

__all__ = ["make_tokenizer", "Token", "LexerError"]

import re


class LexerError(Exception):
    def __init__(self, place, msg):
        self.place = place
        self.msg = msg

    def __str__(self):
        s = "cannot tokenize data"
        line, pos = self.place
        return '%s: %d,%d: "%s"' % (s, line, pos, self.msg)


class Token(object):
    """A token object that represents a substring of certain type in your text.

    You can compare tokens for equality using the `==` operator. Tokens also define
    custom `repr()` and `str()`.

    Attributes:
        type (str): User-defined type of the token (e.g. `"name"`, `"number"`,
            `"operator"`)
        value (str): Text value of the token
        start (Optional[Tuple[int, int]]): Start position (_line_, _column_)
        end (Optional[Tuple[int, int]]): End position (_line_, _column_)
    """

    def __init__(self, type, value, start=None, end=None):
        """Initialize a `Token` object."""
        self.type = type
        self.value = value
        self.start = start
        self.end = end

    def __repr__(self):
        return "Token(%r, %r)" % (self.type, self.value)

    def __eq__(self, other):
        # FIXME: Case sensitivity is assumed here
        if other is None:
            return False
        else:
            return self.type == other.type and self.value == other.value

    def _pos_str(self):
        if self.start is None or self.end is None:
            return ""
        else:
            sl, sp = self.start
            el, ep = self.end
            return "%d,%d-%d,%d:" % (sl, sp, el, ep)

    def __str__(self):
        s = "%s %s '%s'" % (self._pos_str(), self.type, self.value)
        return s.strip()

    @property
    def name(self):
        return self.value

    def pformat(self):
        return "%s %s '%s'" % (
            self._pos_str().ljust(20),  # noqa
            self.type.ljust(14),
            self.value,
        )


def make_tokenizer(specs):
    # noinspection GrazieInspection
    """Make a function that tokenizes text based on the regexp specs.

    Type: `(Sequence[Tuple[str, Tuple[Any, ...]]]) -> Callable[[str], Iterable[Token]]`

    A token spec is a tuple of (_type_, _args_), where _type_ sets the value of
    `Token.type` for a found token, and _args_ are the positional arguments for
    `re.compile()`: either just (_pattern_,) or (_pattern_, _flags_).

    It returns a tokenizer function that takes a string and returns an iterable of
    `Token` objects, or raises `LexerError` if it cannot tokenize the string according
    to its token specs.

    Examples:

    ```pycon
    >>> tokenize = make_tokenizer([
    ...     ("space", (r"\\s+",)),
    ...     ("id", (r"\\w+",)),
    ...     ("op", (r"[,!]",)),
    ... ])
    >>> text = "Hello, World!"
    >>> [t for t in tokenize(text) if t.type != "space"]  # noqa
    [Token('id', 'Hello'), Token('op', ','), Token('id', 'World'), Token('op', '!')]
    >>> text = "Bye?"
    >>> list(tokenize(text))
    Traceback (most recent call last):
        ...
    lexer.LexerError: cannot tokenize data: 1,4: "Bye?"

    ```
    """
    compiled = [(name, re.compile(*args)) for name, args in specs]

    def match_specs(s, i, position):
        line, pos = position
        for type, regexp in compiled:
            m = regexp.match(s, i)
            if m is not None:
                value = m.group()
                nls = value.count("\n")
                n_line = line + nls
                if nls == 0:
                    n_pos = pos + len(value)
                else:
                    n_pos = len(value) - value.rfind("\n") - 1
                return Token(type, value, (line, pos + 1), (n_line, n_pos))
        else:
            err_line = s.splitlines()[line - 1]
            raise LexerError((line, pos + 1), err_line)

    def f(s):
        length = len(s)
        line, pos = 1, 0
        i = 0
        while i < length:
            t = match_specs(s, i, (line, pos))
            yield t
            line, pos = t.end
            i += len(t.value)

    return f


# This is an example of a token spec. See also [this article][1] for a
# discussion of searching for multiline comments using regexps (including `*?`).
#
#   [1]: http://ostermiller.org/findcomment.html
_example_token_specs = [
    ("COMMENT", (r"\(\*(.|[\r\n])*?\*\)", re.MULTILINE)),
    ("COMMENT", (r"\{(.|[\r\n])*?\}", re.MULTILINE)),
    ("COMMENT", (r"//.*",)),
    ("NL", (r"[\r\n]+",)),
    ("SPACE", (r"[ \t\r\n]+",)),
    ("NAME", (r"[A-Za-z_][A-Za-z_0-9]*",)),
    ("REAL", (r"[0-9]+\.[0-9]*([Ee][+\-]?[0-9]+)*",)),
    ("INT", (r"[0-9]+",)),
    ("INT", (r"\$[0-9A-Fa-f]+",)),
    ("OP", (r"(\.\.)|(<>)|(<=)|(>=)|(:=)|[;,=\(\):\[\]\.+\-<>\*/@\^]",)),
    ("STRING", (r"'([^']|(''))*'",)),
    ("CHAR", (r"#[0-9]+",)),
    ("CHAR", (r"#\$[0-9A-Fa-f]+",)),
]
# tokenize = make_tokenizer(_example_token_specs)
