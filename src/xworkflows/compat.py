# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois
# This code is distributed under the two-clause BSD License.

import sys

is_python3 = (sys.version_info[0] >= 3)

if is_python3:
    from collections.abc import Callable

    def u(text, errors=''):
        return str(text)

    def is_string(var):
        return isinstance(var, str)
else:
    from collections import Callable

    def u(text, errors=''):
        return unicode(text, 'utf8', errors)  # noqa: F821

    def is_string(var):
        return isinstance(var, basestring)  # noqa: F821


def is_callable(var):
    return isinstance(var, Callable)
