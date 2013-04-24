# -*- coding: utf-8 -*-

r"""A DOT language parser using funcparserlib.

The parser is based on [the DOT grammar][1]. It is pretty complete with a few
not supported things:

* String ecapes `\"`
* Ports and compass points
* XML identifiers

At the moment, the parser builds only a parse tree, not an abstract syntax tree
(AST) or an API for dealing with DOT.

  [1]: http://www.graphviz.org/doc/info/lang.html
"""

import sys
import os
from re import MULTILINE
from funcparserlib.util import pretty_tree
from funcparserlib.lexer import make_tokenizer, Token, LexerError
from funcparserlib.parser import (some, a, maybe, many, finished, skip,
                                  oneplus, forward_decl, NoParseError)

try:
    from collections import namedtuple
except ImportError:
    # Basic implementation of namedtuple for 2.1 < Python < 2.6
    def namedtuple(name, fields):
        """Only space-delimited fields are supported."""

        def prop(i, name):
            return name, property(lambda self: self[i])

        def new(cls, *args, **kwargs):
            args = list(args)
            n = len(args)
            for i in range(n, len(names)):
                name = names[i - n]
                args.append(kwargs[name])
            return tuple.__new__(cls, args)

        names = dict((i, f) for i, f in enumerate(fields.split(u' ')))
        methods = dict(prop(i, f) for i, f in enumerate(fields.split(u' ')))
        methods.update({
            '__new__': new,
            '__repr__': lambda self: u'%s(%s)' % (
                name,
                u', '.join(u'%s=%r' % (
                    f, getattr(self, f)) for f in fields.split(u' ')))})
        return type(name, (tuple,), methods)

ENCODING = u'UTF-8'

Graph = namedtuple('Graph', 'strict type id stmts')
SubGraph = namedtuple('SubGraph', 'id stmts')
Node = namedtuple('Node', 'id attrs')
Attr = namedtuple('Attr', 'name value')
Edge = namedtuple('Edge', 'nodes attrs')
DefAttrs = namedtuple('DefAttrs', 'object attrs')


def tokenize(str):
    """str -> Sequence(Token)"""
    specs = [
        (u'Comment', (ur'/\*(.|[\r\n])*?\*/', MULTILINE)),
        (u'Comment', (ur'//.*',)),
        (u'NL', (ur'[\r\n]+',)),
        (u'Space', (ur'[ \t\r\n]+',)),
        (u'Name', (ur'[A-Za-z\200-\377_][A-Za-z\200-\377_0-9]*',)),
        (u'Op', (ur'[{};,=\[\]]|(->)|(--)',)),
        (u'Number', (ur'-?(\.[0-9]+)|([0-9]+(\.[0-9]*)?)',)),
        (u'String', (ur'"[^"]*"',)), # '\"' escapes are ignored
    ]
    useless = [u'Comment', u'NL', u'Space']
    t = make_tokenizer(specs)
    return [x for x in t(str) if x.type not in useless]


def parse(seq):
    """Sequence(Token) -> object"""
    unarg = lambda f: lambda args: f(*args)
    tokval = lambda x: x.value
    flatten = lambda list: sum(list, [])
    n = lambda s: a(Token(u'Name', s)) >> tokval
    op = lambda s: a(Token(u'Op', s)) >> tokval
    op_ = lambda s: skip(op(s))
    id_types = [u'Name', u'Number', u'String']
    id = some(lambda t: t.type in id_types).named(u'id') >> tokval
    make_graph_attr = lambda args: DefAttrs(u'graph', [Attr(*args)])
    make_edge = lambda x, xs, attrs: Edge([x] + xs, attrs)

    node_id = id # + maybe(port)
    a_list = (
        id +
        maybe(op_(u'=') + id) +
        skip(maybe(op(u',')))
        >> unarg(Attr))
    attr_list = (
        many(op_(u'[') + many(a_list) + op_(u']'))
        >> flatten)
    attr_stmt = (
        (n(u'graph') | n(u'node') | n(u'edge')) +
        attr_list
        >> unarg(DefAttrs))
    graph_attr = id + op_(u'=') + id >> make_graph_attr
    node_stmt = node_id + attr_list >> unarg(Node)
    # We use a forward_decl becaue of circular definitions like (stmt_list ->
    # stmt -> subgraph -> stmt_list)
    subgraph = forward_decl()
    edge_rhs = skip(op(u'->') | op(u'--')) + (subgraph | node_id)
    edge_stmt = (
        (subgraph | node_id) +
        oneplus(edge_rhs) +
        attr_list
        >> unarg(make_edge))
    stmt = (
        attr_stmt
        | edge_stmt
        | subgraph
        | graph_attr
        | node_stmt
    )
    stmt_list = many(stmt + skip(maybe(op(u';'))))
    subgraph.define(
        skip(n(u'subgraph')) +
        maybe(id) +
        op_(u'{') +
        stmt_list +
        op_(u'}')
        >> unarg(SubGraph))
    graph = (
        maybe(n(u'strict')) +
        maybe(n(u'graph') | n(u'digraph')) +
        maybe(id) +
        op_(u'{') +
        stmt_list +
        op_(u'}')
        >> unarg(Graph))
    dotfile = graph + skip(finished)

    return dotfile.parse(seq)


def pretty_parse_tree(x):
    """object -> str"""
    Pair = namedtuple(u'Pair', u'first second')
    p = lambda x, y: Pair(x, y)

    def kids(x):
        """object -> list(object)"""
        if isinstance(x, (Graph, SubGraph)):
            return [p(u'stmts', x.stmts)]
        elif isinstance(x, (Node, DefAttrs)):
            return [p(u'attrs', x.attrs)]
        elif isinstance(x, Edge):
            return [p(u'nodes', x.nodes), p(u'attrs', x.attrs)]
        elif isinstance(x, Pair):
            return x.second
        else:
            return []

    def show(x):
        """object -> str"""
        if isinstance(x, Pair):
            return x.first
        elif isinstance(x, Graph):
            return u'Graph [id=%s, strict=%r, type=%s]' % (
                x.id, x.strict is not None, x.type)
        elif isinstance(x, SubGraph):
            return u'SubGraph [id=%s]' % (x.id,)
        elif isinstance(x, Edge):
            return u'Edge'
        elif isinstance(x, Attr):
            return u'Attr [name=%s, value=%s]' % (x.name, x.value)
        elif isinstance(x, DefAttrs):
            return u'DefAttrs [object=%s]' % (x.object,)
        elif isinstance(x, Node):
            return u'Node [id=%s]' % (x.id,)
        else:
            return unicode(x)

    return pretty_tree(x, kids, show)


def main():
    #import logging
    #logging.basicConfig(level=logging.DEBUG)
    #import funcparserlib
    #funcparserlib.parser.debug = True
    try:
        stdin = os.fdopen(sys.stdin.fileno(), u'rb')
        input = stdin.read().decode(ENCODING)
        tree = parse(tokenize(input))
        #print pformat(tree)
        print pretty_parse_tree(tree).encode(ENCODING)
    except (NoParseError, LexerError), e:
        msg = (u'syntax error: %s' % e).encode(ENCODING)
        print >> sys.stderr, msg
        sys.exit(1)


if __name__ == '__main__':
    main()
