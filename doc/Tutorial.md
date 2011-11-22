The `funcparserlib` Tutorial
============================

<dl>
  <dt>Author:</dt>
  <dd class="vcard">
    <a class="fn url" href="http://claimid.com/vlasovskikh">Andrey Vlasovskikh</a>
  </dd>
  <dt>License:</dt>
  <dd>
    <a href="http://creativecommons.org/licenses/by-nc-sa/3.0/">
      Creative Commons Attribution-Noncommercial-Share Alike 3.0
    </a>
  </dd>
  <dt>Library Homepage:</dt>
  <dd>
    <a href="http://code.google.com/p/funcparserlib/">
      http://code.google.com/p/funcparserlib/
    </a>
  </dd>
  <dt>Library Version:</dt>
  <dd>0.4dev</dd>
</dl>


Foreword
--------

This is an epic tutorial that explains how to write parsers using
`funcparserlib`. As the tutorial contains lots of code listings, it is written
using the exciting [doctest][] module. This module is a part of the Python
standard library. Using it, you can _execute the tutorial file_ in order to make
sure that all the code listings work as described here.

Although writing functional parsers and functional programming in general is
fun, the large size of the tutorial makes it a bit monotonous. To prevent the
reader from getting bored, some bits of humor and interesting facts were added.

Some knowlegde of general parsing concepts is assumed as well as some
familiarity with functional programming. Experience with Haskell or Scheme would
be nice, but it is not required.

Any comments and suggestions are welcome! Especially corrections related to the
English language, as the author is not a native English speaker. Please post
your comments to [the issues list][funcparserlib-issues] on Google Code.

Contents
--------

1. [Intro](#intro)
2. [Diving In](#diving-in)
3. [Lexing with `tokenize`](#lexing-with-tokenize)
4. [The Library Basics](#library-basics)
    1. [Parser Combinators](#parser-combinators)
    2. [The `some` Combinator](#some-combinator)
    3. [The `>>` Combinator](#rshift-combinator)
    4. [The `+` Combinator](#add-combinator)
5. [Getting First Numbers](#getting-first-numbers)
    1. [The `a` Combinator](#a-combinator)
    2. [Pythonic Uncurrying](#pythonic-uncurrying)
6. [Making a Choice](#making-choice)
    1. [The `|` Combinator](#or-combinator)
    2. [Conflicting Alternatives](#conflicting-alternatives)
    3. [The Fear of Left-Recursion](#fear-of-left-recursion)
    4. [The `many` Combinator](#many-combinator)
7. [Ordering Calculations](#ordering-calculations)
    1. [Operator Precedence](#operator-precedence)
    2. [The `with_forward_decls` Combinator](#with-forward-decls-combinator)
8. [Polishing the Code](#polishing-code)
    1. [The `skip` Combinator](#skip-combinator)
    2. [The `finished` Combinator](#finished-combinator)
    3. [The `maybe` Combinator](#maybe-combinator)
9. [Advanced Topics](#advanced-topics)
    1. [Parser Type Classes](#parser-type-classes)
    2. [Papers on Funcional Parsers](#papers-on-functional-parsers)


<h2 id="intro">Intro</h2>

In this tutorial, we will write _an expression calculator_ that uses syntax
similar to Python or Haskell expressions. Writing a calculator is a common
example in articles related to parsers and parsing techniques, so it is a good
starting point in learning `funcparserlib`.

If you are interested in more real-world examples, see the sources of [a
GraphViz DOT parser][dot-parser] or [a JSON parser][json-parser] available in
`./examples` directory of `funcparserlib`. If you need just a short intro
instead of the full tutorial, see the [Nested Brackets Mini-HOWTO][nested].

We will show how to write a parser and an evaluator of expressions using
`funcparserlib`. The library comes with its own lexer module, but in this
example we will use the standard Python module [tokenize][] as a lexer.
`funcparserlib` parser combinators are completely agnostic of what the tokens
are and how they have been produced, so you can use any lexer you like.

Here are some expressions we want to be able to parse and calculate:

    1
    2 + 3
    2 ** 32 - 1
    3.1415926 * (2 + 7.18281828e-1)


<h2 id="diving-in">Diving In</h2>

Here is a complete expression calculator program.

You are not assumed to understand it now. Just look at its shape and try to get
some feeling of its structure.

In the end of this tutorial you will fully understand this code and will be able
to write parsers for your own needs.

    :::python

    >>> from StringIO import StringIO
    >>> from tokenize import generate_tokens
    >>> import operator, token
    >>> from funcparserlib.parser import (some, a, many, skip, finished, maybe,
    ...     with_forward_decls)

    >>> class Token(object):
    ...     def __init__(self, code, value, start=(0, 0), stop=(0, 0), line=''):
    ...         self.code = code
    ...         self.value = value
    ...         self.start = start
    ...         self.stop = stop
    ...         self.line = line
    ...
    ...     @property
    ...     def type(self):
    ...         return token.tok_name[self.code]
    ...
    ...     def __unicode__(self):
    ...         pos = '-'.join('%d,%d' % x for x in [self.start, self.stop])
    ...         return "%s %s '%s'" % (pos, self.type, self.value)
    ...
    ...     def __repr__(self):
    ...         return 'Token(%r, %r, %r, %r, %r)' % (
    ...             self.code, self.value, self.start, self.stop, self.line)
    ...
    ...     def __eq__(self, other):
    ...         return (self.code, self.value) == (other.code, other.value)

    >>> def tokenize(s):
    ...     'str -> [Token]'
    ...     return list(Token(*t)
    ...         for t in generate_tokens(StringIO(s).readline)
    ...         if t[0] not in [token.NEWLINE])

    >>> def parse(tokens):
    ...     'Sequence(Token) -> int or float or None'
    ...     # Well known functions
    ...     const = lambda x: lambda _: x
    ...     unarg = lambda f: lambda x: f(*x)
    ...
    ...     # Semantic actions and auxiliary functions
    ...     tokval = lambda tok: tok.value
    ...     makeop = lambda s, f: op(s) >> const(f)
    ...     def make_number(s):
    ...         try:
    ...             return int(s)
    ...         except ValueError:
    ...             return float(s)
    ...     def eval_expr(z, list):
    ...         'float, [((float, float -> float), float)] -> float'
    ...         return reduce(lambda s, (f, x): f(s, x), list, z)
    ...     eval = unarg(eval_expr)
    ...
    ...     # Primitives
    ...     number = (
    ...         some(lambda tok: tok.code == token.NUMBER)
    ...         >> tokval
    ...         >> make_number)
    ...     op = lambda s: a(Token(token.OP, s)) >> tokval
    ...     op_ = lambda s: skip(op(s))
    ...
    ...     add = makeop('+', operator.add)
    ...     sub = makeop('-', operator.sub)
    ...     mul = makeop('*', operator.mul)
    ...     div = makeop('/', operator.div)
    ...     pow = makeop('**', operator.pow)
    ...
    ...     mul_op = mul | div
    ...     add_op = add | sub
    ...
    ...     # Means of composition
    ...     @with_forward_decls
    ...     def primary():
    ...         return number | (op_('(') + expr + op_(')'))
    ...     factor = primary + many(pow + primary) >> eval
    ...     term = factor + many(mul_op + factor) >> eval
    ...     expr = term + many(add_op + term) >> eval
    ...
    ...     # Toplevel parsers
    ...     endmark = a(Token(token.ENDMARKER, ''))
    ...     end = skip(endmark + finished)
    ...     toplevel = maybe(expr) + end
    ...
    ...     return toplevel.parse(tokens)

A couple of tests:

    :::python

    >>> assert parse(tokenize('')) is None
    >>> assert parse(tokenize('1')) == 1
    >>> assert parse(tokenize('2 + 3')) == 5
    >>> assert parse(tokenize('2 * (3 + 4)')) == 14

OK, now let's forget about all this stuff:

    :::python

    >>> del StringIO, generate_tokens, operator, token
    >>> del Token, tokenize, parse

and start from scratch!


<h2 id="lexing-with-tokenize">Lexing with <code>tokenize</code></h2>

We start with lexing in order to be able to define parsers in terms of tokens,
not just characters. This section is auxiliary and it is completely unrelated to
`funcparserlib`. But we just need tokens to start writing parsers. You may skip
this section and start with &ldquo;The Library Basics&rdquo;.

We will need to `generate_tokens` using the standard `tokenize` module:

    :::python

    >>> from tokenize import generate_tokens

Import some standard library stuff:

    :::python

    >>> from StringIO import StringIO
    >>> from pprint import pformat

This is an output from the tokenizer:

    :::python

    >>> ts = list(generate_tokens(StringIO('3 * (4 + 5)').readline))
    >>> print pformat(ts)
    [(2, '3', (1, 0), (1, 1), '3 * (4 + 5)'),
     (51, '*', (1, 2), (1, 3), '3 * (4 + 5)'),
     (51, '(', (1, 4), (1, 5), '3 * (4 + 5)'),
     (2, '4', (1, 5), (1, 6), '3 * (4 + 5)'),
     (51, '+', (1, 7), (1, 8), '3 * (4 + 5)'),
     (2, '5', (1, 9), (1, 10), '3 * (4 + 5)'),
     (51, ')', (1, 10), (1, 11), '3 * (4 + 5)'),
     (0, '', (2, 0), (2, 0), '')]

As we can see, the lexer has already thrown away the spaces. Each token is a
5-tuple of the token code, the token string, the beginning and ending of the
token, the line on which it was found.

Let's make the output more pretty by wrapping a token in a class. We could
definitely go on without such a wrapper, but it will make messages more readable
and allow access to the fields of the token by name.

Import a standard module containing the code-to-name map for tokens:

    :::python

    >>> import token

Define the wrapper class:

    :::python

    >>> class Token(object):
    ...     def __init__(self, code, value, start=(0, 0), stop=(0, 0), line=''):
    ...         self.code = code
    ...         self.value = value
    ...         self.start = start
    ...         self.stop = stop
    ...         self.line = line
    ...
    ...     @property
    ...     def type(self):
    ...         return token.tok_name[self.code]
    ...
    ...     def __unicode__(self):
    ...         pos = '-'.join('%d,%d' % x for x in [self.start, self.stop])
    ...         return "%s %s '%s'" % (pos, self.type, self.value)
    ...
    ...     def __repr__(self):
    ...         return 'Token(%r, %r, %r, %r, %r)' % (
    ...             self.code, self.value, self.start, self.stop, self.line)
    ...
    ...     def __eq__(self, other):
    ...         return (self.code, self.value) == (other.code, other.value)

Functions `__repr__` and `__eq__` will be used later. Let's see what it will
look like:

    :::python

    >>> print '\n'.join(unicode(Token(*t)) for t in ts)
    1,0-1,1 NUMBER '3'
    1,2-1,3 OP '*'
    1,4-1,5 OP '('
    1,5-1,6 NUMBER '4'
    1,7-1,8 OP '+'
    1,9-1,10 NUMBER '5'
    1,10-1,11 OP ')'
    2,0-2,0 ENDMARKER ''

So we are basically done with lexing. The last thing left is to write _the_
lexer function:

    :::python

    >>> def tokenize(s):
    ...     'str -> [Token]'
    ...     return list(Token(*t)
    ...         for t in generate_tokens(StringIO(s).readline)
    ...         if t[0] not in [token.NEWLINE])

Here we just have added filtering newline symbols.


<h2 id="library-basics">The Library Basics</h2>

`funcparserlib` is a library for recursive descent parsing using parser
combinators. The parsers made with its help are LL(*) parsers. It means that
it's very easy to write them without thinking about look-aheads and all that
hardcore parsing stuff. But the recursive descent parsing is a rather slow
method compared to LL(k) or LR(k) algorithms. So the primary domain for
`funcparserlib` is parsing small languages or external DSLs (domain specific
languages).


<h3 id="parser-combinators">Parser Combinators</h3>

_A parser_ is basically a function `f` of type (we will use a Haskell-ish
notation for types):

    f :: [a] -> (b, [a])

that takes a list of tokens of arbitrary type `a` and returns a pair of the
parsed value of arbitrary type `b` and the list of tokens left. We can define
an alias for this type:

    type Parser(a, b) = [a] -> (b, [a])

_Parser combinators_ are just higher-order functions that take parsers as their
arguments and return them as result values. Parser combinators are:

* First-class values
* Extremely composable
* Tend to make the code quite compact
* Resemble the readable notation of xBNF grammars

`funcparserlib` uses a more advanced parser type in order to generalize away
from lists to [sequences][] and provide more readable error reports by tracking
a parsing state (in a functional way of course):

    f :: Sequence(a), State -> (b, State)

But this parser type is no fun any more. In order to get rid of it as well as to
use overloaded operators `funcparserlib` wraps parser functions into a class (we
have already seen this approach earlier in the lexer). This class is named
`Parser` and all the combinators we will be using deal with objects of this
class. So the typedef `Parser(a, b)` above is just a parameterized class, not a
function. The parser itself is ivoked via `Parser.run` function.

In fact, all the plain parser functions are hidden from you by `funcparserlib`
so you don't need to know these internals. So, every parser `p` you have ever
met `isinstance` of the `Parser` class.

So let's leave parser functions behind the barrier of abstraction. But if you
are interested in how all this stuff really works, just look into [the
sources][parser-py] of `funcparserlib`! There are only approximately 300 lines
of documented code there. And you are already familiar with the basic idea.


<h3 id="some-combinator">The <code>some</code> Combinator</h3>

Initial imports:

    :::python

    >>> from funcparserlib.parser import some, a, many, skip, finished, maybe

Let's recall the expressions we would like to parse:

    1
    2 + 3
    2 ** 32 - 1
    3.1415926 * (2 + 7.18281828e-1)

So our grammar consists of expressions, that consist of numbers or nested
expressions. All the expressions we have seen so far are binary.

Let's start with just numbers. Number is some token of type `'NUMBER'`:

    :::python

    >>> number = some(lambda tok: tok.type == 'NUMBER')

We have just introduced the first parser combinator &mdash; `some`. Dealing with
parser combinators, we should always keep in mind their types in order to know
precisely what they do. `some` has the following type:

    some :: (a -> bool) -> Parser(a, a)

`some` takes as its input a predicate function from token of arbitrary type `a`
and returns a parser of `Sequence(a)` that returns a result of type `a`. The
first `a` in `Parser` is the type of tokens in the input sequence, and the
second one is the type of a parsed token. The type doesn't change during
parsing, so we get exaclty the token that satisfies the predicate (there is only
one function from `a` to `a`: `id = lambda x: x`).

The resulting parser acts like a filter by parsing only those tokens that
satisfy the predicate. Hence the name: _some_ token satisfying the predicate
will be returned by the parser.

And this is how it works:

    :::python

    >>> number.parse(tokenize('5'))
    Token(2, '5', (1, 0), (1, 1), '5')

and how it reports errors:

    :::python

    >>> number.parse(tokenize('a'))
    Traceback (most recent call last):
        ...
    ParserError: got unexpected token: 1,0-1,1 NAME 'a'

Notice that the lexer and the `Token` wrapper class help us identify the
position in which the error occured.


<h3 id="rshift-combinator">The <code>&gt;&gt;</code> Combinator</h3>

Using `some`, we have got a parsed `Token`. But we need numbers, not `Token`s, to
calculate an expression! So the result of the `number` parser is not
appropriate. It should have the type `int` or `float`. We need some tool to
transform a `Parser(Token, Token)` into a `Parser(Token, int or float)` (note:
we use dynamic typing here).

And this tool is called the `>>` combinator. It has the type:

    (>>) :: Parser(a, b), (b -> c) -> Parser(a, c)

Again, its type suggests what it can possibly do. It returns a parser, that
applies the `Parser(a, b)` to the input sequence and then maps the result of
type `b` to type `c` using a function `b -> c` (for functionally inclined: a
parser is a functor where `>>` is its `fmap`).

Let's write a function that maps a `Token` to an `int` or a `float`:

    :::python

    >>> def make_number(tok):
    ...     'Token -> int or float'
    ...     try:
    ...         return int(tok.value)
    ...     except ValueError:
    ...         return float(tok.value)

OK, but we can spilt this one into two more primitive useful functions:

    :::python

    >>> def tokval(tok):
    ...     'Token -> str'
    ...     return tok.value

    >>> def make_number(s):
    ...     try:
    ...         return int(s)
    ...     except ValueError:
    ...         return float(s)

Let's use these functions in our `number` parser:

    :::python

    >>> number = (
    ...     some(lambda tok: tok.type == 'NUMBER')
    ...     >> tokval
    ...     >> make_number)

Now we got exactly what we needed:

    :::python

    >>> number.parse(tokenize('5'))
    5
    >>> '%g' % number.parse(tokenize('1.6e-19'))
    '1.6e-19'

See how composition works. We compose a parser `some(...)` of type
`Parser(Token, Token)` with the function `tokval` and we get a value of type
`Parser` again, but this time it is `Parser(Token, str)`. Let's put it this way:
the set of parsers is closed under the application of `>>` to a parser and a
function of type `a -> b`.


<h3 id="add-combinator">The <code>+</code> Combinator</h3>

Having just numbers is boring. We need some operations on them. Let's start with
the only one operator `**` (because `+` could be confusing in this context) and
apply it to numbers only, not to expressions.

In the expression `2 ** 32`, we need some way of saying &ldquo;a number `2` is
followed by an operator `**`, followed by a number `32`.&rdquo; In
`funcparserlib`, we do this by using the `+` combinator.

The `+` combinator is a sequential composition of two parsers. It has the
following type (warning: dynamic typing tricks ahead):

    (+) :: Parser(a, b), Parser(a, c) -> Parser(a, _Tuple(b, c))

It basically does the following. Given two parsers of `Sequence(a)` to `b` and
`c`, respectively, it returns a parser, that applies the first one to the
sequence, then applies the second one to the sequence left, and combines the
results into a `_Tuple`.

The `_Tuple` is some sort of magic that simplifies access to the parsing
results. It accumulates all the parsed values preventing the nesting of tuples.
We can &ldquo;turn off&rdquo; the `_Tuple` to see what will happen by
explicitely casing every value parsed by a composed parser to `tuple`:

    :::python

    >>> p = (number + number >> tuple) + number >> tuple
    >>> p.parse(tokenize('1 2 3'))
    ((1, 2), 3)

We have got nested tuples. To get the first number from the result `t` we need
to use `t[0][0]`. The second and the third ones are `t[0][1]` and `t[1]`. Well,
it is pretty inconsistent (but it is OK for you, Lisp hackers).

So the magic does the following:

    :::python

    >>> p = number + number + number
    >>> p.parse(tokenize('1 2 3'))
    (1, 2, 3)

Now it's OK for everyone (except for very statically typed persons).

OK, let's write a parser for the power operator expression. We have already got
a number parser. Now we need an operator parser. How about this one:

    :::python

    >>> pow = some(lambda tok: tok.type == 'OP' and tok.value == '**') >> tokval

It will work, but let's abstract away from the operator name:

    :::python

    >>> def op(s):
    ...     'str -> Parser(Token, str)'
    ...     return (
    ...         some(lambda tok: tok.type == 'OP' and tok.value == s)
    ...         >> tokval)


<h2 id="getting-first-numbers">Getting First Numbers</h2>

<h3 id="a-combinator">The <code>a</code> Combinator</h3>

Continuing with the `op`, we can define it using `lambda`:

    :::python

    >>> op = (lambda s:
    ...     some(lambda tok: tok.type == 'OP' and tok.value == s)
    ...     >> tokval)

We need to parse here an exact token, a token `s`. So maybe we can come up with
some combinator, that takes as its input a value and returns a parser, that
parses a token only if it is equal to that value. Let's call this combinator `a`
(because it parses _a_ token given to it). Here is its type:

    a :: Eq(a) => a -> Parser(a, a)

`a` requires an equality constraint (we have already defined `__eq__` for
`Token`) on its input type `a`.

The definition of the combinator is straightforward:

    :::python

    a = lambda x: some(lambda y: x == y)

It's quite useful in practice, so `funcparserlib` already contains such a
combinator. You can just import it from there (as we have already done earlier).

Let's rewrite `op` using `a`:

    :::python

    >>> op = lambda s: a(Token(token.OP, s)) >> tokval
    >>> pow = op('**')

and test it:

    :::python

    >>> pow.parse(tokenize('**'))
    '**'

Oops, we got just a string `'**'`, but we wanted a function `**` (for Lisp
hackers: it would be nice to just `(eval (quote **))`). We have already seen
this problem before. Let's just transform the parser using `>>`:

    :::python

    >>> import operator
    >>> pow = op('**') >> (lambda x: operator.pow)

OK, but the `x` isn't used here, so the classic function `const` comes to our
minds (for combinatorically inclined: it is just `K`):

    :::python

    >>> const = lambda x: lambda _: x

The revisited version of `pow` is:

    :::python

    >>> pow = op('**') >> const(operator.pow)

Let's test it again:

    :::python

    >>> f = pow.parse(tokenize('**'))
    >>> f(2, 12)
    4096
    >>> del f


<h3 id="pythonic-uncurrying">Pythonic Uncurrying</h3>

OK, it's time to put it all together. Let's define the `eval_expr` function,
that will map the result of parsing an expression to the resulting value:

    :::python

    >>> def eval_expr(x):
    ...     return x[1](x[0], x[2])

Then define a simple expression parser (we don't recur on the subparts of the
expression yet):

    :::python

    >>> expr = number + pow + number >> eval_expr

Test it:

    :::python

    >>> expr.parse(tokenize('2 ** 12'))
    4096

Cool! Our first real calculation!

But the `eval_expr` function isn't very clean. Why doesn't it just take
positional arguments instead of a tuple? Because `+` returns a tuple (the magic
`_Tuple`). Hey, don't allow some code to force you to make your functions less
clean than they should be!

Let's make the arguments positional and provide a wrapper for calling
`eval_expr` with a single tuple. In fact, this task is quite general. We can
turn any function of `n` arguments into a function of a single `n`-tuple (for
functionally inclined: we can uncurry it):

    :::python

    >>> unarg = lambda f: lambda x: f(*x)

So the new `eval_expr` is:

    :::python

    >>> eval_expr = unarg(lambda a, f, b: f(a, b))

Yes, it is cleaner now than it was before.

Redefine `expr` and test it:

    :::python

    >>> expr = number + pow + number >> eval_expr
    >>> expr.parse(tokenize('2 ** 12'))
    4096


<h2 id="making-choice">Making a Choice</h2>

<h3 id="or-combinator">The <code>|</code> Combinator</h3>

So far so good. Now we need to support more than one operation. We already know
how define a new operation. But how do we choose between, say, `**` and `-`
while parsing? The combinators we learned so far are pretty determinate. Well,
except for `some` that returns something that satisfies the predicate. In this
particular case we could continue with only `some`, but this approach is _ad
hoc_ so we need a general one.

And the general approach is the choice combinator `|`. It allows choice
composition of parsers.  Given two parsers of `Sequence(a)` returning `b` and
`c`, respectively, it returns a parser of `Sequence(a)` that applies the first
parser, and in case it has failed applies the second one. Here is it's type (for
Haskell hackers: dynamic typing again, there should be `Either b c` here):

    (|) :: Parser(a, b), Parser(a, c) -> Parser(a, b or c)

Let's see how it works by defining one more operator:

    :::python

    >>> sub = op('-') >> const(operator.sub)

and then using the choice combinator in `expr`:

    :::python

    >>> expr = number + (pow | sub) + number >> eval_expr

Test it:

    :::python

    >>> expr.parse(tokenize('2 ** 8'))
    256
    >>> expr.parse(tokenize('256 - 1'))
    255

and what if none of the alternatives matches:

    :::python

    >>> expr.parse(tokenize('2 + 2'))
    Traceback (most recent call last):
        ...
    ParserError: got unexpected token: 1,2-1,3 OP '+'

Let's cover all the basic arithmetic binary operators using one more bit of
abstraction:

    :::python

    >>> makeop = lambda s, f: op(s) >> const(f)

    >>> add = makeop('+', operator.add)
    >>> sub = makeop('-', operator.sub)
    >>> mul = makeop('*', operator.mul)
    >>> div = makeop('/', operator.div)
    >>> pow = makeop('**', operator.pow)

    >>> operator = add | sub | mul | div | pow
    >>> expr = number + operator + number >> eval_expr

Test it:

    :::python

    >>> expr.parse(tokenize('2 + 2'))
    4
    >>> expr.parse(tokenize('2 * 2'))
    4

Yay! We can do elementary school arithmetics!


<h3 id="conflicting-alternatives">Conflicting Alternatives</h3>

OK, we have got a parser for expressions containing a binary operation, so we
can write a toplevel parser of single numbers _and_ expressions of numbers:

    >>> toplevel = number | expr

Test it:

    :::python

    >>> toplevel.parse(tokenize('5'))
    5
    >>> toplevel.parse(tokenize('2 + 3')) == 5
    False
    >>> toplevel.parse(tokenize('2 + 3'))
    2

Oops, it does wrong arithmetics! We have encountered a common problem in
parsing. The first alternative of `toplevel` parses a subtree of some next
alternative (because `number` is a subpart of `expr`).  We should be careful and
compose parsers using `|` so that they don't conflict with each other:

    :::python

    >>> toplevel = expr | number

Remember that the longest token sequence should be parsed first!

Let's test it:

    :::python

    >>> toplevel.parse(tokenize('5'))
    5
    >>> toplevel.parse(tokenize('2 + 3'))
    5


<h3 id="fear-of-left-recursion">The Fear of Left-Recursion</h3>

We have defined the `toplevel` parser, that can parse expressions of numbers or
just numbers. But what about expressions of expressions of numbers, etc.? We
want to be able to parse the following expression:

    2 ** 32 - 1

In order to build (or evaluate) its parse tree we could write a recurive parser:

    expr = (expr + operator + expr) | number

but we cannot, because in top-down parsing algorithms (like the one used in
`funcparserlib`) left-recursion leads to non-termination of parsing!

How to avoid left-recursion on `expr` here? Let's start thinking in terms of
EBNF (Extended Backus-Naur Form) that is used widely in grammar definitions. Our
parser corresponds to these EBNF productions:

    :::ebnf

    <expr>     ::= <rec-expr> | <number> ;
    <rec-expr> ::= <expr> , <operator> , <expr> ;

Left-recursion is still there of course. But we can rewrite them this way using
EBNF repetition syntax:

    :::ebnf

    <expr> ::= <number> , { <operator> , <number> }

Here `{` and `}` mean &ldquo;zero or more times&rdquo;. As we can see,
left-recursion has been thrown away here. It is always possible to get rid of it
using a formal method, but usually you can just look at your grammar and
modify it a little to make it non-left-recursive.

Remember that the left-recursion must be avoided!

<h3 id="many-combinator">The <code>many</code> Combinator</h3>

The new definition of `<expr>` doesn't have left-recurison any more, but it
assumes a new parser combinator for doing things many times as supposed by the
`{` `}` notation.

This combinator is called `many`. It returns a parser that applies a parser
passed as its argument to a sequence of tokens as many times as the parser
succeeds. The resulting parser returns a list of results containing zero or more
parsed tokens. Here is its type:

    many :: Parser(a, b) -> Parser(a, [b])

It works like this:

    :::python

    >>> many(number).parse(tokenize('1'))
    [1]
    >>> many(number).parse(tokenize('1 2 3'))
    [1, 2, 3]
    >>> many(number).parse(tokenize('1 foo'))
    [1]
    >>> many(number).parse(tokenize('foo'))
    []

With `many`, we can avoid left-recursion and translate the `<expr>` production
of EBNF directly into the parser of `funcparserlib`:

    :::python

    >>> expr = number + many(operator + number)

Let's test it:

    :::python

    >>> expr.parse(tokenize('2 + 3'))
    (2, [(<built-in function add>, 3)])

It seems that we forgot to map parsing results to numbers again.  Let's fix
this:

    :::python

    >>> def eval_expr(z, list):
    ...     return reduce(lambda s, (f, x): f(s, x), list, z)

Here we fold the `list` of an operator an its right operand starting with the
initial value `z` using a function that applies the operator `f` to the
accumulated value `s` and the right operand `x` (for functionally inclined: we
just `foldl` the list of functions and their right arguments using function
application).

Well, for _not_ functionally inclined: just write your own `eval_expr` for
evaluating results of the new `expr` and then look how your recursion pattern is
abstracted in the code above.

Now let's refine `expr` with `eval_expr`:

    :::python

    >>> expr = number + many(operator + number) >> unarg(eval_expr)

and test it:

    :::python

    >>> expr.parse(tokenize('2 * 3 + 4'))
    10
    >>> expr.parse(tokenize('1 * 2 * 3 * 4'))
    24

Cool, we just have calculated the factorial of 4!

    :::python

    >>> expr.parse(tokenize('2 ** 32 - 1')) == 4294967295
    True

and this is the largest `unsigned int` possible on 32-bit computers.


<h2 id="ordering-calculations">Ordering Calculations</h2>

<h3 id="operator-precedence">Operator Precedence</h3>

And how about this one:

    :::python

    >>> expr.parse(tokenize('2 + 3 * 4'))
    20

Wait, it should be `14`, not `20`, because `2 + 3 * 4` is really `2 + (3 * 4)`.
Our parser is unaware of operators precedence.

There are two basic approaches for dealing with precedence in parsers. The first
one is to provide special constructs for specifying precedence and the second
one is to modify the grammar to reflect the precedence rules. We will use the
second one.

According to this quite popular approach, our modified grammar will look like
this:

    :::python

    >>> f = unarg(eval_expr)

    >>> mul_op = mul | div
    >>> add_op = add | sub

    >>> factor = number + many(pow + number) >> f
    >>> term = factor + many(mul_op + factor) >> f
    >>> expr = term + many(add_op + term) >> f

The nesting levels in the parse tree mirror the precedence levels of the
operators. So `1` as a tree is something like `Expr(Term(Factor(Number(1))))`
but its OK since it's only a parse tree, not an AST (abstract syntax tree). In a
typical AST, such wrapper nodes are thrown away. We don't transform our parse
tree into an AST because we write an interpreter that evaluates parse tree nodes
(does semantic actions) while parsing.

Let's test our new `expr`:

    :::python

    >>> expr.parse(tokenize('1'))
    1
    >>> expr.parse(tokenize('2 + 3 * 4'))
    14
    >>> expr.parse(tokenize('3 + 2 * 2 ** 3 - 4 * 4'))
    3


<h3 id="with-forward-decls-combinator">The <code>with_forward_decls</code>
Combinator</h3>

Initial deletions:

    :::python

    >>> del expr

The last thing we want to see in our expressions is parentheses. That's an easy
one. Let's just add one more nesting level of operators. Parentheses have the
highest precedence, so they should be nested in `factor`. We can write the new
nested parser `primary`:

    :::python

    >>> primary = number | ((op('(') + expr + op(')')) >> (lambda x: x[1]))
    Traceback (most recent call last):
        ...
    NameError: name 'expr' is not defined

Oops, if fact, we cannot yet! The definition is recursive. `primary` uses
`expr`, but `expr` uses `term` that uses `factor` that uses `primary`.

Variable binding rules in Python don't allow using a variable before it got
assigned a value in the current scope. But it's OK to use it within a nested
scope, think of mutually recursive functions definitions. So we have to wrap the
parser that is assigned to `primary` into a function of no arguments (sometimes
called a suspension or a thunk) in order to evaluate the parser lazily (for
Haskell hackers: you got it for free, lazy guys).

Such a combinator is provided by `funcparserlib`. It is called
`with_forward_decls` and its type is:

    with_forward_decls :: (None -> Parser(a, b)) -> Parser(a, b)

Import it:

    :::python

    >>> from funcparserlib.parser import with_forward_decls

Another way to define mutually recursive parsers is via the `forward_decl`
combinator. It uses some bits of mutable state, but it is more efficient and
probably will be the recommended way to deal with recursive definitions. See the
sources for details. But let's use `with_forward_decls` here.

Finally, we can write a definition of `primary` that has a forward declaration
of `expr`:

    :::python

    >>> primary = with_forward_decls(lambda:
    ...     number | ((op('(') + expr + op(')')) >> (lambda x: x[1])))

or equivalently using Python decorators syntax:

    :::python

    >>> @with_forward_decls
    ... def primary():
    ...     return number | ((op('(') + expr + op(')')) >> (lambda x: x[1]))

and redefine the dependent parsers:

    :::python

    >>> factor = primary + many(pow + primary) >> f
    >>> term = factor + many(mul_op + factor) >> f
    >>> expr = term + many(add_op + term) >> f

Let's test it:

    :::python

    >>> expr.parse(tokenize('2 + 3 * 4'))
    14
    >>> expr.parse(tokenize('(2 + 3) * 4'))
    20
    >>> expr.parse(tokenize('((1 + 1) ** (((8))))'))
    256

So, we are basically done with our expression parser. But there are still some
minor issues we want to cover.

One not so minor thing we still don't have in our expressions is the unary `-`
for negative numbers. Its implementation is left as an exercise for the reader
(for Haskell hackers: you may wish to add functions support to our calculator
and implement `-` as a function `negate`).


<h2 id="polishing-code">Polishing the Code</h2>

Let's cover some minor issues we mentioned in the previous section.


<h3 id="skip-combinator">The <code>skip</code> Combinator</h3>

First of all, the parentheses parser we have defined is quite ugly:

    :::python

    primary = with_forward_decls(lambda:
        number | ((op('(') + expr + op(')')) >> (lambda x: x[1])))

What we really want to say here is: &ldquo;`primary` is a parser
`with_forward_decls`, that parses a `number` or (an `op('(')` followed by an
`expr` followed be an `op(')')`) where `op`s are of no use and should be
skipped, so the return value is just the `number` or the `expr`.&rdquo;

The `skip` combinator will help us to write exactly that. It has the following
type (warning: dynamic typing magic is back again):

    :::python

    skip :: Parser(a, b) -> Parser(a, _Ignored(b))

A magic `_Ignored(b)` value is a trivial container for values of `b` that is
completely ignored by the `+` combinator during concatenation of its magic
`_Tuple` of results.

Look at the examples:

    :::python

    >>> (number + number).parse(tokenize('2 3'))
    (2, 3)
    >>> (skip(number) + number).parse(tokenize('2 3'))
    3
    >>> (skip(number) + number).parse(tokenize('+ 2 3'))
    Traceback (most recent call last):
        ...
    ParserError: got unexpected token: 1,0-1,1 OP '+'

Note, that `skip` still requires its argument parser to succeed.

So let's rewrite the `primary` parser using `op_` (for Haskell hackers: notice
a naming analogy with functions like `sequence_`):

    :::python

    >>> op_ = lambda s: skip(op(s))

    >>> primary = with_forward_decls(lambda:
    ...     number | (op_('(') + expr + op_(')')))

and redefine the dependent parsers:

    :::python

    >>> factor = primary + many(pow + primary) >> f
    >>> term = factor + many(mul_op + factor) >> f
    >>> expr = term + many(add_op + term) >> f

Finally, test it:

    :::python

    >>> expr.parse(tokenize('(2 + 3) * 4'))
    20
    >>> expr.parse(tokenize('3.1415926 * (2 + 7.18281828e-1)'))
    8.5397340755592719


<h3 id="finished-combinator">The <code>finished</code> Combinator</h3>

It seems that we have almost finished with our calculator. Let's fix some more
subtle problems. Suppose the user typed the following string:

    :::python

    '2 + 3 * 4 foo'

It seems like a syntax error: `'foo'` is clearly not a part of our expression
grammar. Let's test it:

    :::python

    >>> expr.parse(tokenize('2 + 3 foo'))
    5

No, it _is_ a part of our grammar somehow. Let's look at the sequence of tokens
in this example:

    :::python

    >>> print '\n'.join(map(unicode, tokenize('2 + 3 foo')))
    1,0-1,1 NUMBER '2'
    1,2-1,3 OP '+'
    1,4-1,5 NUMBER '3'
    1,6-1,9 NAME 'foo'
    2,0-2,0 ENDMARKER ''

Our `expr` parses the first three tokens and then stops calculating the result.
Why does it behave this way? Let's recall the type of a parser function (that is
hidden inside `Parser`):

    p :: Sequence(a), State -> (b, State)

A parser function takes tokens from the input sequence and transforms them into
a tuple of a resulting value of type `b` _and_ the rest of the input sequence.
The `Parser.parse` function that we are using drops the rest of the sequence and
returns only the resulting value. Hence, only the first three tokens were parsed
in our example.

So we need some means to make sure that the input sequence is parsed to its very
end. There are two things we have to do. The first one is to consume the
`ENDMARKER` token returned by `tokenize.generate_tokens`. And the second one is
to check that nothing is left in the stream.

Checking the `ENDMARKER` is easy:

    :::python

    >>> endmark = a(Token(token.ENDMARKER, ''))
    >>> toplevel = expr + skip(endmark)

Test it:

    :::python

    >>> toplevel.parse(tokenize('2 + 3 foo'))
    Traceback (most recent call last):
        ...
    ParserError: got unexpected token: 1,6-1,9 NAME 'foo'
    >>> toplevel.parse(tokenize('2 + 3'))
    5

Now we need to check that nothing is left in the sequence after the `ENDMARKER`.
In the context of a parser _function_ it is easy again. We have to check the
lengh of the input sequence. Let's call it `finished`:

    :::python

    @Parser
    def finished(tokens, s):
        if len(tokens) == 0:
            return (None, s)
        else:
            raise NoParseError('sequence must be empty', s)

Notice, that the function is wrapped into a `Parser` object.

But functions like this one expose too many internal details. In fact, we have
managed so far without dealing with all these `Parser` and `NoParseError`
classes, manipulations with a parsing state, etc. So it is a rare case when we
really need the details.

As this particular parser is useful in practice, it is provided by
`funcparserlib` so we can just import it and forget about the internals of
parsers again.

Let's rewrite `toplevel` again:

    :::python

    >>> toplevel = expr + skip(endmark + finished)
    >>> toplevel.parse(tokenize('2 + 3'))
    5

Test is using a hand crafted illegal sequence of tokens:

    :::python

    >>> toplevel.parse([
    ...     Token(token.NUMBER, '5'),
    ...     Token(token.ENDMARKER, ''),
    ...     Token(token.ENDMARKER, '')])
    Traceback (most recent call last):
        ...
    ParserError: should have reached <EOF>: 0,0-0,0 ENDMARKER ''


<h3 id="maybe-combinator">The <code>maybe</code> Combinator</h3>

And what about the empty input:

    :::python

    >>> toplevel.parse(tokenize(''))
    Traceback (most recent call last):
        ...
    ParserError: got unexpected token: 1,0-1,0 ENDMARKER ''

In a calculator (as in any shell) the empty string should be considered as a
no-op command. The result should be nothing, not an error message.

Let's allow the empty input in `toplevel`:

    :::python

    >>> end = skip(endmark + finished)
    >>> toplevel = (end >> const(None)) | (expr + end)

Why `>> const(None)`, not just `end`? Because `skip` returns a value of type
`_Ignored(a)` and we need just `None`.

Test it:

    :::python

    >>> toplevel.parse(tokenize('2 + 3'))
    5
    >>> toplevel.parse(tokenize('')) is None
    True

`toplevel` is now correct, but its definition uses too many words. Basically we
want to say just this: &ldquo;`toplevel` consists of an optional `expr`, plus
the `end` of the input.&rdquo; This reminds us of optional production brackets
`[` `]` in EBNF. In an EBNF grammar, we can write:

    :::ebnf

    <toplevel> ::= [ <expr> ] , <end>

Why not just add the equivalent `maybe` combinator to our tools? `funcparserlib`
already includes `maybe`, and it is quite useful in practice.

But let's try to come up with its definition ourselves!

We could write the following `_maybe` combinator, that returns a parser
returning either the result of the given parser or `None` if the parser fails:

    :::python

    >>> _maybe = lambda x: x | (some(const(True)) >> const(None))

The first alternative is the parser that is to be made optional and the second
one is the parser that always succeeds (it isn't so, see below) and returns
`None`.

Test it:

    :::python

    >>> _maybe(op('(')).parse(tokenize('()'))
    '('
    >>> (_maybe(op('(')) + number).parse(tokenize('5'))
    Traceback (most recent call last):
        ...
    ParserError: got unexpected token: 2,0-2,0 ENDMARKER ''

Oops, it doesn't work! The reason is that `some(const(True))` always consumes
one token despite the fact that the predicate `const(True)` doesn't require a
token. We need some parser that does nothing and keeps its input untouched
returning its argument as a result. It is called the `pure` combinator (for
functionally inclined: a parser is a pointed functor). Here is its type:

    pure :: b -> Parser(a, b)

`pure` itself is not so useful in practice. But the real `maybe` combinator from
`funcparserlib` is defined in terms if `pure`:

    :::python

    maybe = lambda x: x | pure(None)

We will just import `maybe` from `funcparserlib` (we have already done this in
the beginning). Here is its type (for Haskell hackers: yes, it should return
`Maybe b`):

    :::python

    maybe :: Parser(a, b) -> Parser(a, b or None)

Given `maybe`, let's rewrite `toplevel` once again. But this time we are about
to define an interface function for parsing as we did for lexing:

    :::python

    >>> def parse(tokens):
    ...     'Sequence(Token) -> int or float or None'
    ...
    ...     # All our parsers should be defined here
    ...
    ...     toplevel = maybe(expr) + end
    ...     return toplevel.parse(tokens)

`toplevel` is very nice now!

Let's test it:

    :::python

    >>> parse(tokenize('2 + 3'))
    5
    >>> parse(tokenize('')) is None
    True

Now we have completed our calculator!

Go make yourself a cup of tea and revisit the full source code in the
&ldquo;Dive In&rdquo; section! Or maybe read some advanced materials below.

And don't forget to write some comments [here][funcparserlib-issues]!


<h2 id="advanced-topics">Advanced Topics</h2>

<h3 id="parser-type-classes">Parser Type Classes</h3>

Parsers can be thought as instances of type classes. Parsers are monads
(therefore, applicative pointed functors). The monadic nature of parsers is used
in the implementation of some combinators, see [the source code][parser-py].
Also parsers form two monoids under sequential composition and choice
composition. 

Haskell hackers may have extra fun by considering the following pseudo-Haskell
instances for parsers:

    :::haskell

    instance Functor (Parser a) where
        fmap f x = x >> f

    instance Pointed (Parser a) where
        pure x = pure x

    instance Monad (Parser a b) where
        x >>= f = x.bind(f)

    instance Monoid (Parser a b) where
        mempty = skip(pure(const(None)))
        mappend x y = x + y

    instance Monoid (Parser a b) where
        mempty = some(const(False))
        mappend x y = x | y


  [doctest]: http://docs.python.org/library/doctest.html
  [tokenize]: http://docs.python.org/library/tokenize.html
  [funcparserlib]: http://code.google.com/p/funcparserlib/
  [funcparserlib-issues]: http://code.google.com/p/funcparserlib/issues/list
  [dot-parser]: http://code.google.com/p/funcparserlib/source/browse/examples/dot/dot.py
  [json-parser]: http://code.google.com/p/funcparserlib/source/browse/examples/json/json.py
  [nested]: http://archlinux.folding-maps.org/2009/funcparserlib/Brackets
  [sequences]: http://www.python.org/dev/peps/pep-3119/#sequences
  [parser-py]:  http://code.google.com/p/funcparserlib/source/browse/src/funcparserlib/parser.py


<h3 id="papers-on-functional-parsers">Papers on Functional Parsers</h3>

TODO: There are lots of them. Write a review.

<!-- vim:set ft=markdown: -->

