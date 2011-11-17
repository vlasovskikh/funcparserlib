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

test: unittest examples doctest

doctest:
	make -C doc

examples:
	make -C examples/dot test && \
	make -C examples/json test

unittest:
	nosetests -v

clean:
	$(SETUP) clean
	rm -fr build dist MANIFEST
	find -name '*.pyc' | xargs rm -f

