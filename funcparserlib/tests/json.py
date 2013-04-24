# -*- coding: utf-8 -*-

r"""A JSON parser using funcparserlib.

The parser is based on [the JSON grammar][1].

  [1]: http://tools.ietf.org/html/rfc4627
"""

import sys
import os
import re
import logging
from re import VERBOSE
from pprint import pformat
from funcparserlib.lexer import make_tokenizer, Token, LexerError
from funcparserlib.parser import (some, a, maybe, many, finished, skip,
                                  forward_decl, NoParseError)

ENCODING = u'UTF-8'
regexps = {
    u'escaped': ur'''
        \\                                  # Escape
          ((?P<standard>["\\/bfnrt])        # Standard escapes
        | (u(?P<unicode>[0-9A-Fa-f]{4})))   # uXXXX
        ''',
    u'unescaped': ur'''
        [^"\\]                              # Unescaped: avoid ["\\]
        ''',
}
re_esc = re.compile(regexps[u'escaped'], VERBOSE)


def tokenize(str):
    """str -> Sequence(Token)"""
    specs = [
        (u'Space', (ur'[ \t\r\n]+',)),
        (u'String', (ur'"(%(unescaped)s | %(escaped)s)*"' % regexps, VERBOSE)),
        (u'Number', (ur'''
            -?                  # Minus
            (0|([1-9][0-9]*))   # Int
            (\.[0-9]+)?         # Frac
            ([Ee][+-][0-9]+)?   # Exp
            ''', VERBOSE)),
        (u'Op', (ur'[{}\[\]\-,:]',)),
        (u'Name', (ur'[A-Za-z_][A-Za-z_0-9]*',)),
    ]
    useless = [u'Space']
    t = make_tokenizer(specs)
    return [x for x in t(str) if x.type not in useless]


def parse(seq):
    """Sequence(Token) -> object"""
    const = lambda x: lambda _: x
    tokval = lambda x: x.value
    toktype = lambda t: some(lambda x: x.type == t) >> tokval
    op = lambda s: a(Token(u'Op', s)) >> tokval
    op_ = lambda s: skip(op(s))
    n = lambda s: a(Token(u'Name', s)) >> tokval

    def make_array(n):
        if n is None:
            return []
        else:
            return [n[0]] + n[1]

    def make_object(n):
        return dict(make_array(n))

    def make_number(n):
        try:
            return int(n)
        except ValueError:
            return float(n)

    def unescape(s):
        std = {
            u'"': u'"', u'\\': u'\\', u'/': u'/', u'b': u'\b', u'f': u'\f',
            u'n': u'\n', u'r': u'\r', u't': u'\t',
        }

        def sub(m):
            if m.group(u'standard') is not None:
                return std[m.group(u'standard')]
            else:
                return unichr(int(m.group(u'unicode'), 16))

        return re_esc.sub(sub, s)

    def make_string(n):
        return unescape(n[1:-1])

    null = n(u'null') >> const(None)
    true = n(u'true') >> const(True)
    false = n(u'false') >> const(False)
    number = toktype(u'Number') >> make_number
    string = toktype(u'String') >> make_string
    value = forward_decl()
    member = string + op_(u':') + value >> tuple
    object = (
        op_(u'{') +
        maybe(member + many(op_(u',') + member)) +
        op_(u'}')
        >> make_object)
    array = (
        op_(u'[') +
        maybe(value + many(op_(u',') + value)) +
        op_(u']')
        >> make_array)
    value.define(
        null
        | true
        | false
        | object
        | array
        | number
        | string)
    json_text = object | array
    json_file = json_text + skip(finished)

    return json_file.parse(seq)


def loads(s):
    """str -> object"""
    return parse(tokenize(s))


def main():
    logging.basicConfig(level=logging.DEBUG)
    try:
        stdin = os.fdopen(sys.stdin.fileno(), 'rb')
        input = stdin.read().decode(ENCODING)
        tree = loads(input)
        print pformat(tree)
    except (NoParseError, LexerError), e:
        msg = (u'syntax error: %s' % e).encode(ENCODING)
        print >> sys.stderr, msg
        sys.exit(1)


if __name__ == '__main__':
    main()
