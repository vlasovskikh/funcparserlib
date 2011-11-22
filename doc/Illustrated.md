Parsing Stages Illustrated
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

Given some language, for example, the [GraphViz DOT][dot] graph language (see
[its grammar][dot-grammar]), you can *easily write your own parser* for it in
Python using `funcpaserlib`.

Then you can:

1. Take a piece of source code in this DOT language:

        >>> s = '''\
        ... digraph g1 {
        ...     n1 -> n2 ->
        ...     subgraph n3 {
        ...         nn1 -> nn2 -> nn3;
        ...         nn3 -> nn1;
        ...     };
        ...     subgraph n3 {} -> n1;
        ... }
        ... '''

    that stands for the graph:

    ![The picture of the graph above](test-connected-subgraph.png)

2. Import your small parser (we use one shipped as an example with
    `funcparserlib` here):

        >>> import sys, os
        >>> sys.path.append(os.path.join(os.getcwd(), '../examples/dot'))
        >>> import dot as dotparser

3. Transform the source code into a sequence of tokens:

        >>> toks = dotparser.tokenize(s)

        >>> print '\n'.join(unicode(tok) for tok in toks)
        1,0-1,7: Name 'digraph'
        1,8-1,10: Name 'g1'
        1,11-1,12: Op '{'
        2,4-2,6: Name 'n1'
        2,7-2,9: Op '->'
        2,10-2,12: Name 'n2'
        2,13-2,15: Op '->'
        3,4-3,12: Name 'subgraph'
        3,13-3,15: Name 'n3'
        3,16-3,17: Op '{'
        4,8-4,11: Name 'nn1'
        4,12-4,14: Op '->'
        4,15-4,18: Name 'nn2'
        4,19-4,21: Op '->'
        4,22-4,25: Name 'nn3'
        4,25-4,26: Op ';'
        5,8-5,11: Name 'nn3'
        5,12-5,14: Op '->'
        5,15-5,18: Name 'nn1'
        5,18-5,19: Op ';'
        6,4-6,5: Op '}'
        6,5-6,6: Op ';'
        7,4-7,12: Name 'subgraph'
        7,13-7,15: Name 'n3'
        7,16-7,17: Op '{'
        7,17-7,18: Op '}'
        7,19-7,21: Op '->'
        7,22-7,24: Name 'n1'
        7,24-7,25: Op ';'
        8,0-8,1: Op '}'

4. Parse the sequence of tokens into a parse tree:

        >>> tree = dotparser.parse(toks)

        >>> from textwrap import fill
        >>> print fill(repr(tree), 70)
        Graph(strict=None, type='digraph', id='g1', stmts=[Edge(nodes=['n1',
        'n2', SubGraph(id='n3', stmts=[Edge(nodes=['nn1', 'nn2', 'nn3'],
        attrs=[]), Edge(nodes=['nn3', 'nn1'], attrs=[])])], attrs=[]),
        Edge(nodes=[SubGraph(id='n3', stmts=[]), 'n1'], attrs=[])])

5. Pretty-print the parse tree:

        >>> print dotparser.pretty_parse_tree(tree)
        Graph [id=g1, strict=False, type=digraph]
        `-- stmts
            |-- Edge
            |   |-- nodes
            |   |   |-- n1
            |   |   |-- n2
            |   |   `-- SubGraph [id=n3]
            |   |       `-- stmts
            |   |           |-- Edge
            |   |           |   |-- nodes
            |   |           |   |   |-- nn1
            |   |           |   |   |-- nn2
            |   |           |   |   `-- nn3
            |   |           |   `-- attrs
            |   |           `-- Edge
            |   |               |-- nodes
            |   |               |   |-- nn3
            |   |               |   `-- nn1
            |   |               `-- attrs
            |   `-- attrs
            `-- Edge
                |-- nodes
                |   |-- SubGraph [id=n3]
                |   |   `-- stmts
                |   `-- n1
                `-- attrs

6. And so on. Basically, you got full access to the tree-like structure of the
   DOT file

See [the source code][dot-py] of the DOT parser and the docs at [the funcparserlib
homepage][funcparserlib] for details.

  [dot]: http://www.graphviz.org/
  [dot-grammar]: http://www.graphviz.org/doc/info/lang.html
  [funcparserlib]: http://code.google.com/p/funcparserlib/
  [dot-py]: http://code.google.com/p/funcparserlib/source/browse/examples/dot/dot.py

