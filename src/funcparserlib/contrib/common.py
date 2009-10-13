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

from funcparserlib.lexer import Token
from funcparserlib.parser import a, skip, some

__all__ = [
    'const', 'flatten', 'unarg', 'tokval', 'mktok', 'n', 'op', 'op_', 'sometok',
    'sometoks',
]

# Well-known functions
const = lambda x: lambda _: x
flatten = lambda list: sum(list, [])
unarg = lambda f: lambda args: f(*args)

# Auxiliary functions for lexers
tokval = lambda tok: tok.value

# Auxiliary functions for parsers
mktok = lambda type: lambda s: a(Token(type, s)) >> tokval
n = mktok('name')
op = mktok('op')
op_ = lambda s: skip(op(s))
sometok = lambda type: some(lambda x: x.type == type) >> tokval
sometoks = lambda types: some(lambda x: x.type in types) >> tokval

