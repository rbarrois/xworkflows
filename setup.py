#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois
# This code is distributed under the two-clause BSD License.

import os
import re
import sys

from setuptools import setup

root_dir = os.path.abspath(os.path.dirname(__file__))


def get_version(package_name):
    version_re = re.compile(r"^__version__ = [\"']([\w_.-]+)[\"']$")
    package_components = package_name.split('.')
    path_components = package_components + ['__init__.py']
    with open(os.path.join(root_dir, *path_components)) as f:
        for line in f:
            match = version_re.match(line[:-1])
            if match:
                return match.groups()[0]
    return '0.1.0'


PACKAGE = 'xworkflows'

setup(
    name="xworkflows",
    version=get_version(PACKAGE),
    author="Raphaël Barrois",
    author_email="raphael.barrois+xworkflows@polytechnique.org",
    description=("A library implementing workflows (or state machines) "
        "for Python projects."),
    license="BSD",
    keywords=['workflow', 'state machine', 'automaton'],
    url="https://github.com/rbarrois/xworkflows",
    download_url="https://pypi.python.org/pypi/xworkflows/",
    packages=['xworkflows'],
    setup_requires=[
        'setuptools>=0.8',
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
    ],
    test_suite='tests',
)
