# -*- coding: utf-8 -*-

import sys, os
from re import MULTILINE
from pprint import pformat
from funcparserlib.lexer import make_tokenizer, Token, LexerError
from funcparserlib.parser import (some, a, maybe, many, finished, skip,
    oneplus, NoParseError)

ENCODING = 'utf-8'

def tokenize(str):
    'str -> Sequence(Token)'
    specs = [
        ('Comment', (r'/\*(.|[\r\n])*?\*/', MULTILINE)),
        ('Comment', (r'//.*',)),
        ('NL',      (r'[\r\n]+',)),
        ('Space',   (r'[ \t\r\n]+',)),
        ('Name',    (r'[A-Za-z\200-\377_][A-Za-z\200-\377_0-9]*',)),
        ('Op',      (r'[{};,=\[\]]|(->)|(--)',)),
        ('Number',  (r'-?(\.[0-9]+)|([0-9]+(\.[0-9]*)?)',)),
    ]
    useless = ['Comment', 'NL', 'Space']
    t = make_tokenizer(specs)
    return [x for x in t(str) if x.type not in useless]

def parse(seq):
    'Sequence(Token) -> object'
    # FIXME: Python >= 2.6 only
    from collections import namedtuple
    unarg = lambda f: lambda args: f(*args)
    Graph = unarg(namedtuple('Graph', 'strict type id stmts'))
    Node = unarg(namedtuple('Node', 'id attrs'))
    Attr = unarg(namedtuple('Attr', 'name value'))
    Edge = unarg(namedtuple('Edge', 'id links attrs'))

    tokval = lambda x: x.value
    flatten = lambda list: sum(list, [])
    n = lambda s: a(Token('Name', s)) >> tokval
    op = lambda s: a(Token('Op', s)) >> tokval
    id = some(lambda t: t.type in ['Name', 'Number']).named('id') >> tokval

    node_id = id # + maybe(port)
    a_list = (
        id +
        maybe(skip(op('=')) + id) +
        skip(maybe(op(',')))
        >> Attr)
    attr_list = (
        many(skip(op('[')) + many(a_list) + skip(op(']')))
        >> flatten).named('attr_list')
    node_stmt = (node_id + attr_list >> Node).named('node_stmt')
    edge_rhs = skip(op('->') | op('--')) + node_id
    edge_stmt = (node_id + oneplus(edge_rhs) + attr_list >> Edge).named('edge_stmt')
    stmt = (
        edge_stmt
        | node_stmt
        # | attr_stmt
        # | (id + op('=') + id)
        # | subgraph
    )
    stmt_list = many(stmt + skip(maybe(op(';'))))
    graph = (
        maybe(n('strict')) +
        maybe(n('graph') | n('digraph')) +
        maybe(id) +
        skip(op('{')) +
        stmt_list +
        skip(op('}'))
        >> Graph).named('graph')
    dotfile = graph + skip(finished)

    return dotfile.parse(seq)

def main():
    #import logging
    #logging.basicConfig(level=logging.DEBUG)
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

