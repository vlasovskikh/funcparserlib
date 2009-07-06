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

'''Парсер рекурсивного спуска на основе функциональных комбинаторов.

Основные комбинаторы парсеров взяты из книги Harrison. J. "Introduction to
Functional Programming" и переписаны с ML на Python. См. также
<http://code.google.com/p/funprog-ru/>.

Парсер `p` представляется функцией типа:

    p :: Sequence(a), State -> (b, Sequence(a), State)

принимающей последовательность токенов произвольного типа `a` и возвращающей
функцию, принимающую состояние потока разбора и возвращаюую пару из пары
(разобранный токен произвольного типа `b`, последовательность неразобранных
токенов) и нового состояния разбора.

Далее в библиотеке используется синоним типа этой функции `Parser(a, b)`.

Функции парсеров заворачиваются в объект `Parser`, для которого определны
операторы `+` для последовательного выполнения двух парсеров, `|` для выбора
второго парсера в случае ошибки разбора в первом, `>>` для преобразования
значения, полученного при разборе.

Для упрощения задачи синтаксического анализа и для получения более читаемых
сообщений об ошибках рекомендуется в качестве токенов использовать объекты с
выхода токенизатора, уже включающие в себя, например, информацию о позиции в
коде. В библиотеку входит модуль `funcparserlib.lexer`, для токенизации на
основе регулярных выражений.

Для вывода отладочных сообщений библиотека использует логгер из logging с именем
`"funcparserlib"`.
'''

__all__ = ['Parser', 'NoParseError', 'State', 'finished', 'many', 'some', 'a',
        'several', 'maybe', 'skip', 'oneplus', 'with_forward_decls']

import logging

log = logging.getLogger('funcparserlib')

class State(object):
    '''Состояние разбора потока токенов.

    Хранит текущую позицию в потоке pos и максимально просмотренную позицию max.
    '''
    def __init__(self, pos=0, max=0):
        self.pos = pos
        self.max = max
        
    def __unicode__(self):
        return unicode((self.pos, self.max))

    def __repr__(self):
        return 'State(%r, %r)' % (self.pos, self.max)

class NoParseError(Exception):
    def __init__(self, msg='', state=None):
        self.msg = msg
        self.state = state
    
    def __unicode__(self):
        return self.msg

class Parser(object):
    def __init__(self, p, name=None):
        self.wrapped = p
        if name is not None:
            self.name = name
        else:
            self.name = p.__doc__
        
    def named(self, name):
        'Задаёт имя парсера для более читаемых сообщений.'
        self.name = name
        return self

    def __call__(self, tokens, s):
        'Sequence(a), State -> (b, Sequence(a), State)'
        log.debug('trying rule "%s"' % self.name)
        return self.wrapped(tokens, s)

    def parse(self, tokens):
        '''Sequence(a) -> b

        Вызывает парсер, возвращая только результат разбора. Повышает читаемость
        ошибок разбора за счёт вывода максимальной просмотренной позиции в
        потоке.
        '''
        try:
            (tree, _, _) = self(tokens, State())
            return tree
        except NoParseError, e:
            max = e.state.max
            pos = tokens[max] if len(tokens) > max else '<EOF>'
            raise NoParseError(u'%s: %s' % (e.msg, pos))

    def __add__(self, other):
        '''Parser(a, b), Parser(a, c) -> Parser(a, _Tuple(b, c)*)
        
        Последовательная композиция парсеров.

        NOTE: Настоящий тип разобранного результата не всегда такой.
        Статический тип указать нельзя.
        '''
        @Parser
        def f(tokens, s):
            (v1, r1, s2) = self(tokens, s)
            (v2, r2, s3) = other(r1, s2)
            vs = [v for v in [v1, v2] if not isinstance(v, _Ignored)]
            if len(vs) == 1:
                t = vs[0]
            elif len(vs) == 2 and isinstance(vs[0], _Tuple):
                t = _Tuple(v1 + (v2,))
            else:
                t = _Tuple(vs)
            return (t, r2, s3)
        f.name = '(%s, %s)' % (self.name, other.name)
        return f

    def __or__(self, other):
        '''Parser(a, b), Parser(a, c) -> Parser(a, b | c)
        
        Вариант выбора из двух парсеров.'''
        @Parser
        def f(tokens, s):
            try:
                return self(tokens, s)
            except NoParseError, e:
                return other(tokens, State(s.pos, e.state.max))
        f.name = '(%s | %s)' % (self.name, other.name)
        return f

    def __rshift__(self, f):
        'Parser(a, b), (b -> c) -> Parser(a, c)'
        @Parser
        def g(tokens, s):
            (v, r, s2) = self(tokens, s)
            return (f(v), r, s2)
        g.name = '%s >>' % self.name
        return g

class _Tuple(tuple): pass

class _Ignored(object):
    def __init__(self, value):
        self.value = value

@Parser
def finished(tokens, s):
    '''Parser(a, None)

    Выбрасывает ошибку, если в потоке токенов хоть что-то осталось.
    '''
    if len(tokens) == 0:
        return (None, tokens, s)
    else:
        raise NoParseError('should have reached eof', s)
finished.name = 'finished'

def many(p):
    '''Parser(a, b) -> Parser(a, [b])

    Возвращает пасрсер, многократно применяющий парсер p к потоку, пока p
    успешно разбирает токены, и возвращающий список разобранных значений.
    '''
    @Parser
    def f(tokens, s):
        try:
            (v, next, s2) = p(tokens, s)
            (vs, rest, s3) = many(p)(next, s2)
            return ([v] + vs, rest, s3)
        except NoParseError, e:
            return ([], tokens, e.state)

    @Parser
    def f_iter(tokens, s):
        'Iterative implementation preventing the stack overflow.'
        res = []
        rest = tokens
        try:
            while True:
                (v, rest, s) = p(rest, s)
                res.append(v)
        except NoParseError, e:
            return (res, rest, e.state)
    f_iter.name = '%s +' % p.name
    return f_iter

def some(pred):
    '''(a -> bool) -> Parser(a, a)

    Возвращает парсер, разбирающий токен, который удовлетворяет предикату
    pred.
    '''
    @Parser
    def f(tokens, s):
        if len(tokens) == 0:
            raise NoParseError('no tokens left in the stream', s)
        else:
            t, ts = tokens[0], tokens[1:]
            if pred(t):
                pos = s.pos + 1
                log.debug(u'*matched* "%s", new state = %s' % (
                    t, State(pos, max(pos, s.max))))
                return (t, ts, State(pos, max(pos, s.max)))
            else:
                log.debug(u'failed "%s", state = %s' % (t, s))
                raise NoParseError('got unexpected token', s)
    f.name = '(some ...)'
    return f

def a(value):
    '''a -> Parser(a, a)
    
    Возвращает парсер, разбирающий токен, равный value.
    '''
    return some(lambda t: t == value).named('(a "%s")' % value)

def several(pred):
    '''(a -> bool) -> Parser(a, [a])
    
    Возвращает парсер, разбирающий последовательность токенов,
    удовлетворяющих предикату pred.
    '''
    return many(some(pred))

def maybe(p):
    '''Parser(a, b) -> Parser(a, b | None)

    Возвращает парсер, который при ошибке возвращает None.
    '''
    @Parser
    def f(tokens, s):
        try:
            return p(tokens, s)
        except NoParseError, e:
            return (None, tokens, e.state)
    f.name = '(maybe %s)' % p.name
    return f

def skip(p):
    '''Parser(a, b) -> _Ignored(b)

    Возвращает парсер, результаты работы которого игнорируются комбинатором
    последовательной композиции +.
    '''
    return p >> (lambda x: _Ignored(x))

def oneplus(p):
    '''Parser(a, b) -> Parser(a, [b])

    Возвращает парсер, разбирающий одно или более вхождение токена.
    '''
    return p + many(p) >> (lambda x: [x[0]] + x[1])

def with_forward_decls(suspension):
    '''(None -> Parser(a, b)) -> Parser(a, b)

    Возвращает парсер, лениво вычисляющий требуемый парсер как результат
    suspension. Требуется для определений парсеров, содержащих опережающие
    объявления других парсеров, которые будут определены ниже на уровне этого
    suspension.
    '''
    @Parser
    def f(tokens, s):
        return suspension()(tokens, s)
    return f

