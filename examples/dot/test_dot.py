# -*- coding: utf-8 -*-

from nose.tools import eq_, raises
from funcparserlib.parser import SyntaxError
from dot import parse, tokenize, Graph, Edge, SubGraph, DefAttrs, Attr, Node

def t(data, exptected=None):
    eq_(parse(tokenize(data)), exptected)

def test_comments():
    t(u'''
        /* комм 1 */
        graph /* комм 4 */ g1 {
            // комм 2 /* комм 3 */
        }
        // комм 5
    ''',
    Graph(strict=None, type=u'graph', id=u'g1', stmts=[]))

def test_connected_subgraph():
    t(u'''
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

def test_default_attrs():
    t(u'''
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

def test_empty_graph():
    t(u'''
        graph g1 {}
    ''',
    Graph(strict=None, type=u'graph', id=u'g1', stmts=[]))

def test_few_attrs():
    t(u'''
        digraph g1 {
                n1 [attr1, attr2 = value2];
        }
    ''',
    Graph(strict=None, type=u'digraph', id=u'g1', stmts=[
        Node(id=u'n1', attrs=[
            Attr(name=u'attr1', value=None),
            Attr(name=u'attr2', value=u'value2')])]))

def test_few_nodes():
    t(u'''
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

@raises(SyntaxError)
def test_illegal_comma():
    t(u'''
        graph g1 {
            n1;
            n2;
            n3,
        }
    ''')

@raises(SyntaxError)
def test_null():
    t(u'')

def test_simple_cycle():
    t(u'''
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

@raises(SyntaxError)
def test_single_unicode_char():
    t(u'ф')

def test_unicode_names():
    t(u'''
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

