from nose.tools import eq_
from funcparserlib.parser import a, many

# Issue 31
def test_many_backtracking():
    x = a('x')
    y = a('y')
    expr = many(x + y) + x + x
    eq_(expr.parse('xyxyxx'), ([('x', 'y'), ('x', 'y')], 'x', 'x'))

