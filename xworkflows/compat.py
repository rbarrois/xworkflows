# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois
# Copyright (c) 2021 LinuxForHealth
# This code is distributed under the two-clause BSD License.

from collections.abc import Callable


def u(text, errors=''):
    return str(text)


def is_string(var):
    return isinstance(var, str)


def is_callable(var):
    return isinstance(var, Callable)
