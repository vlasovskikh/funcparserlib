`funcparserlib` FAQ
===================

Frequently asked questions related to [funcparserlib][1].


1. Why did my parser enter an infinite loop?
--------------------------------------------

Because the grammar you've defined allows infinite empty sequences. It's a
general pitfall of grammar rules and it must be avoided. Let's explain why this
may happen.

**Upd:** There is an automatic defense against looping in the tip version of
`funcpaserlib`. It raises an exception telling you to fix your grammar.

_A universally successful parser_ is a parser that _may consume no token_ from
the input sequence _returning a value_ without raising `NoParseError`. It still
may consume some tokens and return values, but when it cannot, it just returns
a value, not an error.

The basic parser combinators that return parsers having this property are
`pure`, `maybe`, and `many`:

* A result of `pure` always returns its argument without even accessing the
  input sequence
* A result of `maybe` always returns either a parsing result or `None`
* A result of `many` always returns a list (maybe the empty one)

By using these combinators for composing parsers you can (and you have done this
actually!) create your own universally successful parsers.

One more fact. Given some parser `p`, the `many` combinator returns a parser `q`
that applies `p` to the input sequence unless `p` fails with `NoParseError`.

So we can deduce that, given a universally successful parser, `many` returns a
parser that may apply it to the input _forever._ This is the cause of an infinite
loop.

You **must not** pass a universally successful parser to the `many` combinator.

Consider the following parsers:

    from funcparserlib.parser import a, many, maybe, pure

    const = lambda x: lambda _: x
    x = a('x')

    p1 = maybe(x)
    p2 = many(p1)
    p3 = maybe(x) + x
    p4 = many(p3)
    p5 = x | many(x)
    p6 = many(p5)
    p7 = x + many(p4)
    p8 = x >> const(True)
    p9 = pure(True)

Here `p1`, `p2`, `p4`, `p5`, `p6`, and `p9` are universally successful parsers
while `p3`, `p7`, and `p8` are is not. Parsers `p2`, `p6`, and `p7` may enter an
infinite loop, while others cannot. Just apply the statements we have made
above to these parsers to figure out why.


2. A `GrammarError` tells that my parser does not halt. What does it mean?
--------------------------------------------------------------------------

It's an automatic defense against infinite loops caused by passing a universally
successful parser to the `many` combinator. See Item 1 of this FAQ.

  [1]: http://code.google.com/p/funcparserlib/

