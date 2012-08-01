# coding: utf-8
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
