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

__all__ = ['tokenize', 'Token', 'LexerError']

import re

class LexerError(Exception):
    def __init__(self, place, str):
        self.place = place
        self.str = str
        
    def __unicode__(self):
        s = 'cannot tokenize data'
        return '%s: %d,%d: "%s"' % (s, self.place[0], self.place[1], self.str)

class Token(object):
    def __init__(self, type, value, start=None, end=None):
        self.type = type
        self.value = value
        self.start = start
        self.end = end

    def __repr__(self):
        return 'Token(%r, %r)' % (self.type, self.value)

    def __eq__(self, other):
        # FIXME: Case sensitivity is assumed here
        return (self.type == other.type
            and self.value == other.value)

    def _pos_str(self):
        if self.start is None or self.end is None:
            return ''
        else:
            sl, sp = self.start
            el, ep = self.end
            return '%d,%d-%d,%d:' % (sl, sp, el, ep)

    def __unicode__(self):
        s = "%s %s '%s'" % (self._pos_str(), self.type, self.value)
        return s.strip()
    
    def pformat(self):
        return "%s %s '%s'" % (self._pos_str().ljust(20),
            self.type.ljust(14), self.value)

def make_tokenizer(specs):
    '[(str, (str, int?))] -> (str -> Iterable(Token))'
    # TODO: Revisit the token spec, e.g. introduce a class for it in order to
    # set options via named arguments of the constructor
    def compile_spec(spec):
        name, args = spec
        return name, re.compile(*args)
    compiled = [compile_spec(s) for s in specs]
    def match_specs(specs, str, i, (line, pos)):
        for type, regexp in specs:
            m = regexp.match(str, i)
            if m is not None:
                value = str[m.start():m.end()]
                nls = value.count(u'\n')
                n_line = line + nls
                if nls == 0:
                    n_pos = pos + len(value)
                else:
                    n_pos = len(value) - value.rfind(u'\n') - 1
                return Token(type, value, (line, pos), (n_line, n_pos))
        else:
            raise LexerError((line, pos), str.split(u'\n', 1)[0])
    def f(str):
        length = len(str)
        line, pos = 1, 0
        i = 0
        while i < length:
            t = match_specs(compiled, str, i, (line, pos))
            yield t
            line, pos = t.end
            i = i + len(t.value)
    return f


# This is an example of a token spec. See also [this article][1] for a
# discussion of searching for multiline comments using regexps (including `*?`).
#
#   [1]: http://ostermiller.org/findcomment.html
_example_token_specs = [
    ('COMMENT', (r'\(\*(.|[\r\n])*?\*\)', re.MULTILINE)),
    ('COMMENT', (r'\{(.|[\r\n])*?\}', re.MULTILINE)),
    ('COMMENT', (r'//.*',)),
    ('NL',      (r'[\r\n]+',)),
    ('SPACE',   (r'[ \t\r\n]+',)),
    ('NAME',    (r'[A-Za-z_][A-Za-z_0-9]*',)),
    ('REAL',    (r'[0-9]+\.[0-9]*([Ee][+\-]?[0-9]+)*',)),
    ('INT',     (r'[0-9]+',)),
    ('INT',     (r'\$[0-9A-Fa-f]+',)),
    ('OP',      (r'(\.\.)|(<>)|(<=)|(>=)|(:=)|[;,=\(\):\[\]\.+\-<>\*/@\^]',)),
    ('STRING',  (r"'([^']|(''))*'",)),
    ('CHAR',    (r'#[0-9]+',)),
    ('CHAR',    (r'#\$[0-9A-Fa-f]+',)),
]
#tokenize = make_tokenizer(_example_token_specs)

