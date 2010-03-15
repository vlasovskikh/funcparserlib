# -*- coding: utf-8 -*-

# Copyright (c) 2008/2009 Andrey Vlasovskikh
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

__all__ = ['make_tokenizer', 'Spec', 'Token', 'LexerError']

import re
from funcparserlib.util import SyntaxError, pos_to_str

class LexerError(SyntaxError):
    def __init__(self, msg, pos):
        SyntaxError.__init__(self, u'cannot tokenize data: "%s"' % msg, pos)

class Token(object):
    def __init__(self, type, value, pos=None):
        self.type = type
        self.value = value
        self.pos = pos

    def __repr__(self):
        return 'Token(%r, %r)' % (self.type, self.value)

    def __eq__(self, other):
        # FIXME: Case sensitivity is assumed here
        return (self.type == other.type
            and self.value == other.value)

    def __unicode__(self):
        s = u"%s '%s'" % (self.type, self.value)
        return s.strip()

    def __str__(self):
        return unicode(self).encode()

    def pformat(self):
        return u"%s %s '%s'" % (pos_to_str(self.pos).ljust(20),
            self.type.ljust(14), self.value)

    @property
    def name(self):
        return self.value

class Spec(object):
    def __init__(self, type, regexp, flags=0):
        self.type = type
        self._regexp = regexp
        self._flags = flags
        # Maybe the regexp should be compiled lazily
        self.re = re.compile(regexp, flags)

    def __repr__(self):
        return 'Spec(%r, %r, %r)' % (self.type, self._regexp, self._flags)

def make_tokenizer(specs):
    '[Spec] -> (str -> Iterable(Token))'
    def match_specs(specs, str, i, (line, pos)):
        for spec in specs:
            m = spec.re.match(str, i)
            if m is not None:
                value = m.group()
                nls = value.count(u'\n')
                n_line = line + nls
                if nls == 0:
                    n_pos = pos + len(value)
                else:
                    n_pos = len(value) - value.rfind(u'\n') - 1
                return Token(spec.type, value, ((line, pos + 1), (n_line, n_pos)))
        else:
            errline = str.splitlines()[line - 1]
            raise LexerError(errline, ((line, pos + 1), (line, len(errline))))
    def f(str):
        length = len(str)
        line, pos = 1, 0
        i = 0
        while i < length:
            t = match_specs(specs, str, i, (line, pos))
            yield t
            _, end = t.pos
            line, pos = end
            i = i + len(t.value)
    return f

# This is an example of a token spec. See also [this article][1] for a
# discussion of searching for multiline comments using regexps (including `*?`).
#
#   [1]: http://ostermiller.org/findcomment.html
_example_token_specs = [
    Spec('comment', r'\(\*(.|[\r\n])*?\*\)', re.MULTILINE),
    Spec('comment', r'\{(.|[\r\n])*?\}', re.MULTILINE),
    Spec('comment', r'//.*'),
    Spec('nl',      r'[\r\n]+'),
    Spec('space',   r'[ \t\r\n]+'),
    Spec('name',    r'[A-Za-z_][A-Za-z_0-9]*'),
    Spec('real',    r'[0-9]+\.[0-9]*([Ee][+\-]?[0-9]+)*'),
    Spec('int',     r'[0-9]+'),
    Spec('int',     r'\$[0-9A-Fa-f]+'),
    Spec('op',      r'(\.\.)|(<>)|(<=)|(>=)|(:=)|[;,=\(\):\[\]\.+\-<>\*/@\^]'),
    Spec('string',  r"'([^']|(''))*'"),
    Spec('char',    r'#[0-9]+'),
    Spec('char',    r'#\$[0-9A-Fa-f]+'),
]
#tokenize = make_tokenizer(_example_token_specs)

