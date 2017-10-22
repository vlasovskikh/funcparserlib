# -*- coding: utf-8 -*-

from setuptools import setup


setup(
    name='funcparserlib',
    version='0.3.6',
    packages=['funcparserlib'],
    author='Andrey Vlasovskikh',
    author_email='andrey.vlasovskikh@gmail.com',
    description='Recursive descent parsing library based on functional '
        'combinators',
    license='MIT',
    url='https://github.com/vlasovskikh/funcparserlib',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers'
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*",
    tests_require=["six"],
)
