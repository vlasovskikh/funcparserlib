# -*- coding: utf-8 -*-

r'''A JSON parser using funcparserlib.

The parser is based on [the JSON grammar][1].

  [1]: http://tools.ietf.org/html/rfc4627
'''

import sys, os, re, logging
from re import VERBOSE
from pprint import pformat
from funcparserlib.lexer import make_tokenizer, Token, LexerError
from funcparserlib.parser import (some, a, maybe, many, finished, skip,
    with_forward_decls, NoParseError)

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
        ('String', (ur'"(%(unescaped)s | %(escaped)s)*"' % regexps, VERBOSE)),
        ('Name', (r'[A-Za-z_][A-Za-z_0-9]*',)),
        ('Number', (r'''
            -?                  # Minus
            (0|([1-9][0-9]*))   # Int
            (\.[0-9]+)?         # Frac
            ([Ee][+-][0-9]+)?   # Exp
            ''', VERBOSE)),
        ('Op', (r'[{}\[\]\-,:]',)),
        ('Space', (r'[ \t\r\n]+',)),
    ]
    useless = ['Space']
    t = make_tokenizer(specs)
    return [x for x in t(str) if x.type not in useless]

def parse(seq):
    'Sequence(Token) -> object'
    const = lambda x: lambda _: x
    tokval = lambda x: x.value
    toktype = lambda t: some(lambda x: x.type == t) >> tokval
    op = lambda s: a(Token('Op', s)) >> tokval
    n = lambda s: a(Token('Name', s)) >> tokval
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

    null = (n('null') >> const(None)).named('null')
    true = (n('true') >> const(True)).named('true')
    false = (n('false') >> const(False)).named('false')
    number = (toktype('Number') >> make_number).named('number')
    string = (toktype('String') >> make_string).named('string')
    value = with_forward_decls(
        lambda:
          null
        | true
        | false
        | object
        | array
        | number
        | string).named('value')
    member = (string + skip(op(':')) + value >> tuple).named('member')
    object = (
        skip(op('{')) +
        maybe(member + many(skip(op(',')) + member)) +
        skip(op('}'))
        >> make_object).named('object')
    array = (
        skip(op('[')) +
        maybe(value + many(skip(op(',')) + value)) +
        skip(op(']'))
        >> make_array).named('array')
    json_text = (object | array).named('json_text')
    json_file = json_text + skip(finished)

    return json_file.parse(seq)

def main():
    logging.basicConfig(level=logging.INFO)
    try:
        stdin = os.fdopen(sys.stdin.fileno(), 'rb')
        input = stdin.read().decode(ENCODING)
        tree = parse(tokenize(input))
        print pformat(tree)
    except (NoParseError, LexerError), e:
        msg = (u'syntax error: %s' % e).encode(ENCODING)
        print >> sys.stderr, msg
        sys.exit(1)

if __name__ == '__main__':
    main()

