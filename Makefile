PYTHON = /usr/bin/python
SETUP = $(PYTHON) setup.py
DESTDIR = /
PREFIX = /usr
INSTALL_OPTS = --root "$(DESTDIR)" --prefix "$(PREFIX)"

.PHONY: default install test doctest unittest examples clean

default:
	$(SETUP) build

install:
	$(SETUP) install $(INSTALL_OPTS)

test: unittest examples

doctest:
	make -C doc

examples:
	$(PYTHON) -m unittest discover examples

unittest:
	$(PYTHON) -m unittest discover tests

clean:
	$(SETUP) clean
	rm -fr build dist MANIFEST
	find -name '*.pyc' | xargs rm -f
	find -name __pycache__ | xargs rm -fr

