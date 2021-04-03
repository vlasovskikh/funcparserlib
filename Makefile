.PHONY: default install test doctest unittest clean poetry-install tox mypy

default: poetry-install
	poetry build

poetry-install:
	poetry install

test: unittest

doctest: poetry-install
	make -C doc

unittest: poetry-install
	poetry run python -m unittest discover

tox:
	poetry run tox

mypy:
	poetry run mypy tests

clean:
	rm -fr build dist *.egg-info .tox
	find . -name '*.pyc' | xargs rm -f
	find . -name __pycache__ | xargs rm -fr
