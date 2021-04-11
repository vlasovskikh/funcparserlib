.PHONY: default install test doctest unittest clean poetry-install tox mypy

default: poetry-install
	poetry build

poetry-install:
	poetry install

test: unittest

tox:
	poetry run tox

clean:
	rm -fr build dist *.egg-info .tox
	find . -name '*.pyc' | xargs rm -f
	find . -name __pycache__ | xargs rm -fr
