# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois
# This code is distributed under the two-clause BSD License.


"""Base components of XWorkflows."""


def iterclass(cls):
    """Iterates over (valid) attributes of a class.

    Args:
        cls (object): the class to iterate over

    Yields:
        (str, obj) tuples: the class-level attributes.
    """
    for field in dir(cls):
        if hasattr(cls, field):
            value = getattr(cls, field)
            yield field, value
