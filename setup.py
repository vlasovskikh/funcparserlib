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
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers'
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    **extra)
