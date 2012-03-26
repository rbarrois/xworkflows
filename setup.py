#!/usr/bin/env python
# coding: utf-8

from distutils.core import setup
from distutils import cmd
import os
import re

def get_version():
    version_re = re.compile(r"^VERSION = '([\w_.]+)'$")
    with open(os.path.join(os.path.dirname(__file__), 'xworkflows', '__init__.py')) as f:
        for line in f:
            match = version_re.match(line[:-1])
            if match:
                return match.groups()[0]
    return '0.0'


class test(cmd.Command):
    """Run the tests for this package."""
    command_name = 'test'
    description = 'run the tests associated with the package'

    user_options = [
        ('test-suite=', None, "A test suite to run (defaults to 'tests')"),
    ]

    def initialize_options(self):
        self.test_runner = None
        self.test_suite = None

    def finalize_options(self):
        self.ensure_string('test_suite', 'tests')

    def run(self):
        """Run the test suite."""
        import unittest
        if self.verbose:
            verbosity=1
        else:
            verbosity=0

        suite = unittest.TestLoader().loadTestsFromName(self.test_suite)

        unittest.TextTestRunner(verbosity=verbosity).run(suite)


setup(
    name="xworkflows",
    version=get_version(),
    author="Raphaël Barrois",
    author_email="raphael.barrois@polyconseil.fr",
    description=("A library implementing workflows (or state machines) "
        "for Python projects."),
    license="BSD",
    keywords=['workflow', 'state machine', 'automaton'],
    url="http://github.com/rbarrois/xworkflows",
    download_url="http://pypi.python.org/pypi/xworkflows/",
    package_dir={'': 'src'},
    packages=['xworkflows'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Topic :: Software Development :: Libraries :: Python Modules",
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    cmdclass={'test': test},
)
