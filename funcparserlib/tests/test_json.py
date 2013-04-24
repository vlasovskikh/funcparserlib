# -*- coding: utf-8 -*-

import unittest
from funcparserlib.parser import NoParseError
from funcparserlib.lexer import LexerError
import json


class JsonTest(unittest.TestCase):
    def t(self, data, expected=None):
        self.assertEqual(json.loads(data), expected)

    def test_1_array(self):
        self.t(u'[1]', [1])

    def test_1_object(self):
        self.t(u'{"foo": "bar"}', {u'foo': u'bar'})

    def test_bool_and_null(self):
        self.t(u'[null, true, false]', [None, True, False])

    def test_empty_array(self):
        self.t(u'[]', [])

    def test_empty_object(self):
        self.t(u'{}', {})

    def test_many_array(self):
        self.t(u'[1, 2, [3, 4, 5], 6]', [1, 2, [3, 4, 5], 6])

    def test_many_object(self):
        self.t(u'''
            {
                "foo": 1,
                "bar":
                {
                    "baz": 2,
                    "quux": [true, false],
                    "{}": {}
                },
                "spam": "eggs"
            }
        ''', {
            u'foo': 1,
            u'bar': {
                u'baz': 2,
                u'quux': [True, False],
                u'{}': {},
            },
            u'spam': u'eggs',
        })

    def test_null(self):
        try:
            self.t(u'')
        except NoParseError:
            pass
        else:
            self.fail('must raise NoParseError')

    def test_numbers(self):
        self.t(u'''\
            [
                0, 1, -1, 14, -14, 65536,
                0.0, 3.14, -3.14, -123.456,
                6.67428e-11, -1.602176e-19, 6.67428E-11
            ]
        ''', [
            0, 1, -1, 14, -14, 65536,
            0.0, 3.14, -3.14, -123.456,
            6.67428e-11, -1.602176e-19, 6.67428E-11,
        ])

    def test_strings(self):
        self.t(ur'''
            [
                ["", "hello", "hello world!"],
                ["привет, мир!", "λx.x"],
                ["\"", "\\", "\/", "\b", "\f", "\n", "\r", "\t"],
                ["\u0000", "\u03bb", "\uffff", "\uFFFF"],
                ["вот функция идентичности:\nλx.x\nили так:\n\u03bbx.x"]
            ]
        ''', [
            [u'', u'hello', u'hello world!'],
            [u'привет, мир!', u'λx.x'],
            [u'"', u'\\', u'/', u'\x08', u'\x0c', u'\n', u'\r', u'\t'],
            [u'\u0000', u'\u03bb', u'\uffff', u'\uffff'],
            [u'вот функция идентичности:\nλx.x\nили так:\n\u03bbx.x'],
        ])

    def test_toplevel_string(self):
        try:
            self.t(u'неправильно')
        except LexerError:
            pass
        else:
            self.fail('must raise LexerError')
