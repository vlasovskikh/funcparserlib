PYTHON = /usr/bin/python
SETUP = $(PYTHON) setup.py
DESTDIR = /
PREFIX = /usr
INSTALL_OPTS = --root "$(DESTDIR)" --prefix "$(PREFIX)"

.PHONY: default install test clean

default:
	$(SETUP) build

install:
	$(SETUP) install $(INSTALL_OPTS)

test:
	make -C examples/dot test && \
	make -C examples/json test && \
	make -C doc test

clean:
	$(SETUP) clean
	rm -fr build dist
	find -name '*.pyc' | xargs rm -f

