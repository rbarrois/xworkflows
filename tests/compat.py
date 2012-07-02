# coding: utf-8

import sys

if sys.version_info[0] <= 2 and sys.version_info[1] < 7:  # pragma: no cover
    import unittest2 as unittest
else:  # pragma: no cover
    import unittest

is_python3 = (sys.version_info[0] >= 3)
