# -*- coding: utf-8 -*-

r'''A JSON parser using funcparserlib.

The parser is based on [the JSON grammar][1].

  [1]: http://tools.ietf.org/html/rfc4627
'''

import sys, os, re, logging
from re import VERBOSE
from pprint import pformat
from funcparserlib.lexer import make_tokenizer, Spec
from funcparserlib.parser import (maybe, many, eof, skip, fwd, name_parser_vars,
        SyntaxError)
from funcparserlib.contrib.common import const, n, op, op_, sometok

ENCODING = 'utf-8'
regexps = {
    'escaped': ur'''
        \\                                  # Escape
          ((?P<standard>["\\/bfnrt])        # Standard escapes
        | (u(?P<unicode>[0-9A-Fa-f]{4})))   # uXXXX
        ''',
    'unescaped': ur'''
        [\x20-\x21\x23-\x5b\x5d-\uffff]     # Unescaped: avoid ["\\]
        ''',
}
re_esc = re.compile(regexps['escaped'], VERBOSE)

def tokenize(str):
    'str -> Sequence(Token)'
    specs = [
        Spec('space', r'[ \t\r\n]+'),
        Spec('string', ur'"(%(unescaped)s | %(escaped)s)*"' % regexps, VERBOSE),
        Spec('number', r'''
            -?                  # Minus
            (0|([1-9][0-9]*))   # Int
            (\.[0-9]+)?         # Frac
            ([Ee][+-][0-9]+)?   # Exp
            ''', VERBOSE),
        Spec('op', r'[{}\[\]\-,:]'),
        Spec('name', r'[A-Za-z_][A-Za-z_0-9]*'),
    ]
    useless = ['space']
    t = make_tokenizer(specs)
    return [x for x in t(str) if x.type not in useless]

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
        '"': '"', '\\': '\\', '/': '/', 'b': '\b', 'f': '\f', 'n': '\n',
        'r': '\r', 't': '\t',
    }
    def sub(m):
        if m.group('standard') is not None:
            return std[m.group('standard')]
        else:
            return unichr(int(m.group('unicode'), 16))
    return re_esc.sub(sub, s)

def make_string(n):
    return unescape(n[1:-1])

# JSON Grammar
null = n('null') >> const(None)
true = n('true') >> const(True)
false = n('false') >> const(False)
number = sometok('number') >> make_number
string = sometok('string') >> make_string
value = fwd()
member = string + op_(':') + value >> tuple
object = (
    op_('{') +
    maybe(member + many(op_(',') + member)) +
    op_('}')
    >> make_object)
array = (
    op_('[') +
    maybe(value + many(op_(',') + value)) +
    op_(']')
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
json_file = json_text + skip(eof)

name_parser_vars(locals())

def parse(seq):
    'Sequence(Token) -> object'
    return json_file.parse(seq)

def loads(s):
    'str -> object'
    return parse(tokenize(s))

def main():
    logging.basicConfig(level=logging.DEBUG)
    try:
        stdin = os.fdopen(sys.stdin.fileno(), 'rb')
        input = stdin.read().decode(ENCODING)
        tree = loads(input)
        print pformat(tree)
    except SyntaxError, e:
        msg = (u'syntax error: %s' % e).encode(ENCODING)
        print >> sys.stderr, msg
        sys.exit(1)

if __name__ == '__main__':
    main()

