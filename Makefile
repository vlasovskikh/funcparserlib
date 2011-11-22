PYTHON = /usr/bin/python2
SETUP = $(PYTHON) setup.py
DESTDIR = /
PREFIX = /usr
INSTALL_OPTS = --root "$(DESTDIR)" --prefix "$(PREFIX)"

.PHONY: default install test unittest doctest examples clean

default:
	$(SETUP) build

install:
	$(SETUP) install $(INSTALL_OPTS)

develop:
	$(SETUP) develop --user

test: unittest examples doctest

unittest:
	nosetests -v

doctest:
	make -C doc

examples:
	make -C examples/dot test && \
	make -C examples/json test

clean:
	$(SETUP) clean
	rm -fr build dist MANIFEST
	find -name '*.pyc' | xargs rm -f

