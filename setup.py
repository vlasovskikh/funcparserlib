# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='funcparserlib',
    version='0.3',
    packages=['funcparserlib'],
    package_dir={'': 'src'},
    author='Andrey Vlasovskikh',
    author_email='andrey.vlasovskikh@gmail.com',
    description='A recursive descent parser library based on functional'
        'combinators',
    license='MIT',
    url='http://code.google.com/p/funcparserlib/')

