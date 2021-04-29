#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) The xworkflows project
# This code is distributed under the two-clause BSD License.

import codecs
import os
import re
import sys

from setuptools import find_packages, setup

root_dir = os.path.abspath(os.path.dirname(__file__))


def get_version():
    version_re = re.compile(r"^__version__ = [\"']([\w_.-]+)[\"']$")
    roots = [root_dir, os.path.join(root_dir, 'src')]
    for root in roots:
        version_path = os.path.join(root_dir, PACKAGE, 'version.py')
        if not os.path.exists(version_path):
            continue
        with codecs.open(version_path, 'r', 'utf-8') as f:
            for line in f:
                match = version_re.match(line[:-1])
                if match:
                    return match.groups()[0]
    return '0.1.0'


def clean_readme(fname):
    """Cleanup README.rst for proper PyPI formatting."""
    with codecs.open(fname, 'r', 'utf-8') as f:
        return ''.join(
            re.sub(r':\w+:`([^`]+?)( <[^<>]+>)?`', r'``\1``', line)
            for line in f
            if not (line.startswith('.. currentmodule') or line.startswith('.. toctree'))
        )


PACKAGE = 'xworkflows'


setup(
    name=PACKAGE,
    version=get_version(),
    author="Raphaël Barrois",
    author_email='raphael.barrois_%s@polytechnique.org' % PACKAGE,
    description="A library implementing workflows (or state machines) for Python projects.",
    long_description=clean_readme('README.rst'),
    license='BSD',
    keywords=['workflow', 'state machine', 'automaton'],
    url='https://github.com/rbarrois/%s' % PACKAGE,
    install_requires=[
    ],
    setup_requires=[
        'setuptools>=1',
    ],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
