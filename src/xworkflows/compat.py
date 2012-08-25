# coding: utf-8

import collections
import sys

is_python3 = (sys.version_info[0] >= 3)

if is_python3:
    def u(text, errors=''):
        return str(text)

    def is_string(var):
        return isinstance(var, str)
else:

    def u(text, errors=''):
        return unicode(text, 'utf8', errors)

    def is_string(var):
        return isinstance(var, basestring)


def is_callable(var):
    return isinstance(var, collections.Callable)
