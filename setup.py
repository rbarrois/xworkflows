#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) The xworkflows project
# This code is distributed under the two-clause BSD License.
# Copyright 2021 (c) LinuxForHealth

import codecs
import os
import re
from importlib.machinery import SourceFileLoader

from setuptools import find_packages, setup

root_dir = os.path.abspath(os.path.dirname(__file__))


def get_version():
    version = SourceFileLoader('version', 'xworkflows/version.py').load_module()
    return version.version


def clean_readme(fname):
    """Cleanup README.md for proper PyPI formatting."""
    with codecs.open(fname, 'r', 'utf-8') as f:
        return ''.join(
            re.sub(r':\w+:`([^`]+?)( <[^<>]+>)?`', r'``\1``', line)
            for line in f
            if not (line.startswith('.. currentmodule') or line.startswith('.. toctree'))
        )


setup(
    name='lfh-xworkflows',
    version=get_version(),
    author="Raphaël Barrois, LinuxForHealth",
    description="LinuxForHealth fork of the XWorkflows project. XWorkflows implements workflows (or state machines) for Python projects.",
    long_description=clean_readme('README.md'),
    long_description_content_type='text/markdown',
    license='BSD',
    keywords=['linuxforhealth', 'lfh', 'workflow', 'state machine', 'automaton'],
    url='https://github.com/LinuxForHealth/xworkflows',
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    extras_require={
        'test': ['pytest==6.1.2'],
        'dev': ['flake8==3.9.0']
    },
    python_requires='>=3.8'
)
