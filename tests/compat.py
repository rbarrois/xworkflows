# coding: utf-8

import sys

if sys.version_info.major <= 2 and sys.version_info.minor < 7:  # pragma: no cover
    import unittest2 as unittest                                # pragma: no cover
else:                                                           # pragma: no cover
    import unittest
