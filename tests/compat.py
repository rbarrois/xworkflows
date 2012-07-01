# coding: utf-8

import sys

if sys.version_info.major <= 2 and sys.version_info.minor < 7:
    import unittest2 as unittest
else:
    import unittest
