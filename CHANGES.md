The Changelog
=============


0.3.6 — 2013-05-02
------------------

### Changed

* Python 3 compatibility
* More info available in exception objects (#14)

### Fixed

* Fixed `many()` that consumed too many tokens in some cases (#31)


0.3.5 — 2011-01-13
------------------

### Changed

* Python 2.4 compatibility
* More readable terminal names for error reporting

### Fixed

* Fixed wrong token positions in lexer error messages


0.3.4 — 2009-10-06
------------------

### Changed

* Switched from `setuptools` to `distutils`
* Improved the `run-tests` utility

### Fixed

* Fixed importing all symbols from `funcparserlib.lexer`


0.3.3 — 2009-08-03
------------------

### Added

* Added a FAQ question about infinite loops in parsers

### Changed

* Debug rule tracing can be enabled again

### Fixed

* Fixed a bug in results of skip + skip parsers


0.3.2 — 2009-07-26
------------------

### Added

* Added the Parsing Stages Illustrated page

### Fixed

* Fixed some string and number encoding issues in examples


0.3.1 — 2009-07-26
------------------

Major optimizations (10x faster than the version 0.3).

### Added

* Added the `forward_decl` function, that performs better than `with_forward_decls`
* Added the `pretty_tree` function for creating pseudo-graphic trees
* Added the Nested Brackets Mini-HOWTO
* Added `Makefile` and this `CHANGES.md` file

### Changed

* Use a single immutable input sequence in parsers
* Call a wrapped parser directly using `run` (without `__call__`)
* The slow `logging` is enabled only when the `debug` flag is set


0.3 — 2009-07-23
----------------

### Added

* Added `pure` and `bind` functions on `Parser`s making them monads
* Added the Funcparserlib Tutorial
* Added a JSON parser as an example

### Changed

* Translated the docs from Russian into English


0.2 — 2009-07-07
----------------

### Added

* Added the `with_forward_decls` combinator for dealing with forward declarations

### Changed

* Switched to the iterative implementation of `many`
* Un-curried the parser function type in order to simplify things
* Improvements to the DOT parser


0.1 — 2009-06-26
----------------

Initial release.
