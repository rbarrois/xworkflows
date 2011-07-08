#!/usr/bin/env python
# coding: utf-8

import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "xworkflows",
    version = "0.1",
    author = "Raphaël Barrois",
    author_email = "raphael.barrois@polyconseil.fr",
    description = ("A library implementing workflows (or state machines) "
        "for Python projects."),
    license = "BSD",
    keywords = "workflow state machine automaton",
    url = "http://packages.python.org/xworkflows",
    package_dir = {'': 'src'},
    packages = ['xworkflows'],
    long_description=read('README.rst'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Topic :: Software Development :: Libraries :: Python Modules",
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    test_suite='tests',
    test_requires=['unittest2'],
)
