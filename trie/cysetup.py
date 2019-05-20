#!/usr/bin/env python

from distutils.core import setup, Extension
from Cython.Distutils import build_ext

setup(
    name='chartrie',
    version='0.1.6',
    description='Given a list of strings, creates a trie to perform fast prefix search.',
    author='Yuri Baburov',
    author_email='burchik@gmail.com',
    cmdclass = {'build_ext': build_ext},
    ext_modules=[Extension('chartrie', ['trie.c', 'chartrie.pyx'])],
)
