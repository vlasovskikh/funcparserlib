# -*- coding: utf-8 -*-

# Copyright (c) 2008/2013 Andrey Vlasovskikh
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

__all__ = ['make_tokenizer', 'Token', 'LexerError']

import re


class LexerError(Exception):
    def __init__(self, place, msg):
        self.place = place
        self.msg = msg

    def __str__(self):
        s = u'cannot tokenize data'
        line, pos = self.place
        return u'%s: %d,%d: "%s"' % (s, line, pos, self.msg)


class Token(object):
    def __init__(self, type, value, start=None, end=None):
        self.type = type
        self.value = value
        self.start = start
        self.end = end

    def __repr__(self):
        return u'Token(%r, %r)' % (self.type, self.value)

    def __eq__(self, other):
        # FIXME: Case sensitivity is assumed here
        return self.type == other.type and self.value == other.value

    def _pos_str(self):
        if self.start is None or self.end is None:
            return ''
        else:
            sl, sp = self.start
            el, ep = self.end
            return u'%d,%d-%d,%d:' % (sl, sp, el, ep)

    def __str__(self):
        s = u"%s %s '%s'" % (self._pos_str(), self.type, self.value)
        return s.strip()

    @property
    def name(self):
        return self.value

    def pformat(self):
        return u"%s %s '%s'" % (self._pos_str().ljust(20),
                                self.type.ljust(14),
                                self.value)


def make_tokenizer(specs):
    """[(str, (str, int?))] -> (str -> Iterable(Token))"""

    def compile_spec(spec):
        name, args = spec
        return name, re.compile(*args)

    compiled = [compile_spec(s) for s in specs]

    def match_specs(specs, str, i, position):
        line, pos = position
        for type, regexp in specs:
            m = regexp.match(str, i)
            if m is not None:
                value = m.group()
                nls = value.count(u'\n')
                n_line = line + nls
                if nls == 0:
                    n_pos = pos + len(value)
                else:
                    n_pos = len(value) - value.rfind(u'\n') - 1
                return Token(type, value, (line, pos + 1), (n_line, n_pos))
        else:
            errline = str.splitlines()[line - 1]
            raise LexerError((line, pos + 1), errline)

    def f(str):
        length = len(str)
        line, pos = 1, 0
        i = 0
        while i < length:
            t = match_specs(compiled, str, i, (line, pos))
            yield t
            line, pos = t.end
            i += len(t.value)

    return f

# This is an example of a token spec. See also [this article][1] for a
# discussion of searching for multiline comments using regexps (including `*?`).
#
#   [1]: http://ostermiller.org/findcomment.html
_example_token_specs = [
    ('COMMENT', (r'\(\*(.|[\r\n])*?\*\)', re.MULTILINE)),
    ('COMMENT', (r'\{(.|[\r\n])*?\}', re.MULTILINE)),
    ('COMMENT', (r'//.*',)),
    ('NL', (r'[\r\n]+',)),
    ('SPACE', (r'[ \t\r\n]+',)),
    ('NAME', (r'[A-Za-z_][A-Za-z_0-9]*',)),
    ('REAL', (r'[0-9]+\.[0-9]*([Ee][+\-]?[0-9]+)*',)),
    ('INT', (r'[0-9]+',)),
    ('INT', (r'\$[0-9A-Fa-f]+',)),
    ('OP', (r'(\.\.)|(<>)|(<=)|(>=)|(:=)|[;,=\(\):\[\]\.+\-<>\*/@\^]',)),
    ('STRING', (r"'([^']|(''))*'",)),
    ('CHAR', (r'#[0-9]+',)),
    ('CHAR', (r'#\$[0-9A-Fa-f]+',)),
]
#tokenize = make_tokenizer(_example_token_specs)
