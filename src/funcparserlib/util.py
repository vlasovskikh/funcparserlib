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

class SyntaxError(Exception):
    'The base class for funcparserlib errors.'
    def __init__(self, msg, pos=None):
        Exception.__init__(self, msg, pos)

    @property
    def pos(self):
        'SyntaxError -> ((int, int), (int, int)) or None'
        return self.args[1]

    def __unicode__(self):
        pos = self.args[1]
        s = u'%s: ' % pos_to_str(pos) if pos is not None else ''
        return u'%s%s' % (s, self.args[0])

    def __str__(self):
        return unicode(self).encode()

def pretty_tree(x, kids, show):
    '''(a, (a -> list(a)), (a -> str)) -> str

    Returns a pseudographic tree representation of x similar to the tree command
    in Unix.
    '''
    (MID, END, CONT, LAST, ROOT) = ('|-- ', '`-- ', '|   ', '    ', '')
    def rec(x, indent, sym):
        line = indent + sym + show(x)
        xs = kids(x)
        if len(xs) == 0:
            return line
        else:
            next_indent = indent + (
                CONT if sym == MID
                     else (ROOT if sym == ROOT else LAST))
            syms = [MID] * (len(xs) - 1) + [END]
            lines = [rec(x, next_indent, sym) for x, sym in zip(xs, syms)]
            return '\n'.join([line] + lines)
    return rec(x, '', ROOT)

def pos_to_str(pos):
    '((int, int), (int, int)) -> str'
    start, end = pos
    sl, sp = start
    el, ep = end
    return '%d,%d-%d,%d' % (sl, sp, el, ep)

