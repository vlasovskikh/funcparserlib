# -*- coding: utf-8 -*-

from setuptools import setup
import sys

extra = {}
if sys.version_info >= (3,):
    extra['use_2to3'] = True


setup(
    name='funcparserlib',
    version='0.3.6',
    packages=['funcparserlib', 'funcparserlib.tests'],
    author='Andrey Vlasovskikh',
    author_email='andrey.vlasovskikh@gmail.com',
    description='Recursive descent parsing library based on functional '
        'combinators',
    license='MIT',
    url='http://code.google.com/p/funcparserlib/',
    **extra)
