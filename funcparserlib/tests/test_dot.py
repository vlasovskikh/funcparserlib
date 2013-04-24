# -*- coding: utf-8 -*-

import unittest
from funcparserlib.parser import NoParseError
from funcparserlib.lexer import LexerError
from dot import parse, tokenize, Graph, Edge, SubGraph, DefAttrs, Attr, Node


class DotTest(unittest.TestCase):
    def t(self, data, expected=None):
        self.assertEqual(parse(tokenize(data)), expected)

    def test_comments(self):
        self.t(u'''
            /* комм 1 */
            graph /* комм 4 */ g1 {
                // комм 2 /* комм 3 */
            }
            // комм 5
        ''',
               Graph(strict=None, type=u'graph', id=u'g1', stmts=[]))

    def test_connected_subgraph(self):
        self.t(u'''
            digraph g1 {
                n1 -> n2 ->
                subgraph n3 {
                    nn1 -> nn2 -> nn3;
                    nn3 -> nn1;
                };
                subgraph n3 {} -> n1;
            }
        ''',
               Graph(strict=None, type=u'digraph', id=u'g1', stmts=[
                   Edge(
                       nodes=[
                           u'n1',
                           u'n2',
                           SubGraph(id=u'n3', stmts=[
                               Edge(
                                   nodes=[u'nn1', u'nn2', u'nn3'],
                                   attrs=[]),
                               Edge(
                                   nodes=[u'nn3', u'nn1'],
                                   attrs=[])])],
                       attrs=[]),
                   Edge(
                       nodes=[
                           SubGraph(id=u'n3', stmts=[]),
                           u'n1'],
                       attrs=[])]))

    def test_default_attrs(self):
        self.t(u'''
            digraph g1 {
                page="3,3";
                graph [rotate=90];
                node [shape=box, color="#0000ff"];
                edge [style=dashed];
                n1 -> n2 -> n3;
                n3 -> n1;
            }
        ''',
               Graph(strict=None, type=u'digraph', id=u'g1', stmts=[
                   DefAttrs(object=u'graph', attrs=[
                       Attr(name=u'page', value=u'"3,3"')]),
                   DefAttrs(object=u'graph', attrs=[
                       Attr(name=u'rotate', value=u'90')]),
                   DefAttrs(object=u'node', attrs=[
                       Attr(name=u'shape', value=u'box'),
                       Attr(name=u'color', value=u'"#0000ff"')]),
                   DefAttrs(object=u'edge', attrs=[
                       Attr(name=u'style', value=u'dashed')]),
                   Edge(nodes=[u'n1', u'n2', u'n3'], attrs=[]),
                   Edge(nodes=[u'n3', u'n1'], attrs=[])]))

    def test_empty_graph(self):
        self.t(u'''
            graph g1 {}
        ''',
               Graph(strict=None, type=u'graph', id=u'g1', stmts=[]))

    def test_few_attrs(self):
        self.t(u'''
            digraph g1 {
                    n1 [attr1, attr2 = value2];
            }
        ''',
               Graph(strict=None, type=u'digraph', id=u'g1', stmts=[
                   Node(id=u'n1', attrs=[
                       Attr(name=u'attr1', value=None),
                       Attr(name=u'attr2', value=u'value2')])]))

    def test_few_nodes(self):
        self.t(u'''
            graph g1 {
                n1;
                n2;
                n3
            }
        ''',
               Graph(strict=None, type=u'graph', id=u'g1', stmts=[
                   Node(id=u'n1', attrs=[]),
                   Node(id=u'n2', attrs=[]),
                   Node(id=u'n3', attrs=[])]))

    def test_illegal_comma(self):
        try:
            self.t(u'''
                graph g1 {
                    n1;
                    n2;
                    n3,
                }
            ''')
        except NoParseError:
            pass
        else:
            self.fail('must raise NoParseError')

    def test_null(self):
        try:
            self.t(u'')
        except NoParseError:
            pass
        else:
            self.fail('must raise NoParseError')

    def test_simple_cycle(self):
        self.t(u'''
            digraph g1 {
                n1 -> n2 [w=5];
                n2 -> n3 [w=10];
                n3 -> n1 [w=7];
            }
        ''',
               Graph(strict=None, type=u'digraph', id=u'g1', stmts=[
                   Edge(nodes=[u'n1', u'n2'], attrs=[
                       Attr(name=u'w', value=u'5')]),
                   Edge(nodes=[u'n2', u'n3'], attrs=[
                       Attr(name=u'w', value=u'10')]),
                   Edge(nodes=[u'n3', u'n1'], attrs=[
                       Attr(name=u'w', value=u'7')])]))

    def test_single_unicode_char(self):
        try:
            self.t(u'ф')
        except LexerError:
            pass
        else:
            self.fail('must raise LexerError')

    def test_unicode_names(self):
        self.t(u'''
            digraph g1 {
                n1 -> "Медведь" [label="Поехали!"];
                "Медведь" -> n3 [label="Добро пожаловать!"];
                n3 -> n1 ["Водка"="Селёдка"];
            }
        ''',
               Graph(strict=None, type=u'digraph', id=u'g1', stmts=[
                   Edge(nodes=[u'n1', u'"Медведь"'], attrs=[
                       Attr(name=u'label', value=u'"Поехали!"')]),
                   Edge(nodes=[u'"Медведь"', u'n3'], attrs=[
                       Attr(name=u'label', value=u'"Добро пожаловать!"')]),
                   Edge(nodes=[u'n3', u'n1'], attrs=[
                       Attr(name=u'"Водка"', value=u'"Селёдка"')])]))
