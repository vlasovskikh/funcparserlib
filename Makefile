.PHONY: default install test doctest unittest clean poetry-install tox

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
	poetry run python -m pip install tox
	poetry run tox

clean:
	rm -fr build dist *.egg-info .tox
	find . -name '*.pyc' | xargs rm -f
	find . -name __pycache__ | xargs rm -fr
