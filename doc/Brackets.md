Nested Brackets Mini-HOWTO
==========================

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


Intro
-----

Let's try out `funcparserlib` using a tiny example: parsing strings of nested
curly brackets. It is well known that it can't be done with regular expressions
so we need a parser. For more complex examples see [The funcparserlib
Tutorial][tutorial] or
other examples at [the funcparserlib homepage][funcparserlib].

  [funcparserlib]: http://code.google.com/p/funcparserlib/
  [tutorial]: http://archlinux.folding-maps.org/2009/funcparserlib/Tutorial

Here is the EBNF grammar of our curly brackets language:

    nested = "{" , { nested } , "}" ;

i. e. `nested` is a sequence of the symbol `{`, followed by zero or more
occurences of the `nested` production itself, followed by the symbol `}`. Let's
develop a parser for this grammar.

We will parse plain strings, but in real life you may wish to use
`funcparserlib.lexer` or any other lexer to tokenize the input and parse tokens,
not just symbols.

We will use the following `funcparserlib` functions: `a`, `forward_decl`,
`maybe`, `finished`, `many`, `skip`, `pretty_tree`. The library actually exports
only 11 functions, so the API is quite compact.


Nested Brackets Checker
-----------------------

Basic usage:

    >>> from funcparserlib.parser import a

    >>> brackets = a('{') + a('}')

    >>> brackets.parse('{}')
    ('{', '}')

Let's write a nested brackets checker:

    >>> from funcparserlib.parser import forward_decl, maybe

    >>> nested = forward_decl()
    >>> nested.define(a('{') + maybe(nested) + a('}'))

Test it:

    >>> nested.parse('{}')
    ('{', None, '}')

    >>> nested.parse('{{}}')
    ('{', ('{', None, '}'), '}')

    >>> nested.parse('{{}')
    Traceback (most recent call last):
        ...
    ParserError: no tokens left in the stream: <EOF>

    >>> nested.parse('{foo}')
    Traceback (most recent call last):
        ...
    ParserError: got unexpected token: f

    >>> nested.parse('{}foo')
    ('{', None, '}')

In the last test we have parsed only a valid subsequence. Let's ensure that all
the input symbols have been parsed:

    >>> from funcparserlib.parser import finished

    >>> input = nested + finished

Test it:

    >>> input.parse('{}foo')
    Traceback (most recent call last):
        ...
    ParserError: should have reached <EOF>: f

Allow zero or more nested brackets:

    >>> from funcparserlib.parser import many

    >>> nested = forward_decl()
    >>> nested.define(a('{') + many(nested) + a('}'))
    >>> input = nested + finished

Test it:

    >>> input.parse('{{}{}}')
    ('{', [('{', [], '}'), ('{', [], '}')], '}', None)

Skip `None`, the result of `finished`:

    >>> from funcparserlib.parser import skip

    >>> end_ = skip(finished)
    >>> input = nested + end_

Test it:

    >>> input.parse('{{}{}}')
    ('{', [('{', [], '}'), ('{', [], '}')], '}')


Textual Parse Tree
------------------

Objectify a parse tree:

    >>> class Bracket(object):
    ...     def __init__(self, kids):
    ...         self.kids = kids
    ...     def __repr__(self):
    ...         return 'Bracket(%r)' % self.kids

    >>> a_ = lambda x: skip(a(x))
    >>> nested = forward_decl()
    >>> nested.define(a_('{') + many(nested) + a_('}') >> Bracket)
    >>> input = nested + end_

Test it:

    >>> nested.parse('{{{}{}}{}}')
    Bracket([Bracket([Bracket([]), Bracket([])]), Bracket([])])

Draw a textual parse tree:

    >>> from funcparserlib.util import pretty_tree

    >>> def ptree(t):
    ...     def kids(x):
    ...         if isinstance(x, Bracket):
    ...             return x.kids
    ...         else:
    ...             return []
    ...     def show(x):
    ...         if isinstance(x, Bracket):
    ...             return '{}'
    ...         else:
    ...             return repr(x)
    ...     return pretty_tree(t, kids, show)

Test it:

    >>> print ptree(nested.parse('{{{}{}}{}}'))
    {}
    |-- {}
    |   |-- {}
    |   `-- {}
    `-- {}

    >>> print ptree(nested.parse('{{{{}}{}}{{}}{}{{}{}}}'))
    {}
    |-- {}
    |   |-- {}
    |   |   `-- {}
    |   `-- {}
    |-- {}
    |   `-- {}
    |-- {}
    `-- {}
        |-- {}
        `-- {}


Nesting Level
-------------

Let's count the nesting level:

    >>> def count(x):
    ...     return 1 if len(x) == 0 else max(x) + 1
    >>> nested = forward_decl()
    >>> nested.define(a_('{') + many(nested) + a_('}') >> count)
    >>> input = nested + end_

Test it:

    >>> input.parse('{}')
    1
    >>> input.parse('{{{}}}')
    3
    >>> input.parse('{{}{{{}}}}')
    4
    >>> input.parse('{{{}}{}}')
    3

<!-- vim: set ft=markdown tw=80: -->

