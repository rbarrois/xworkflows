#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois
# This code is distributed under the two-clause BSD License.

import warnings

from .compat import is_python3, unittest, u

from xworkflows import utils


class IterClassTestCase(unittest.TestCase):
    def test_simple_class(self):
        class MyClass(object):

            x = 42

            def inst_mth(self):  # pragma: no cover
                pass

            @classmethod
            def cls_mth(cls):  # pragma: no cover
                pass

            @staticmethod
            def st_mth(cls):  # pragma: no cover
                pass

        fields = list(utils.iterclass(MyClass))
        self.assertIn(('x', 42), fields)
        self.assertIn(('inst_mth', MyClass.inst_mth), fields)
        self.assertIn(('cls_mth', MyClass.cls_mth), fields)
        self.assertIn(('st_mth', MyClass.st_mth), fields)

    def test_mixed_attr(self):
        """Tests for fields in dir() but whose getattr() fails."""

        class InstanceOnlyDescriptor(object):
            def __get__(self, instance, owner):
                if instance is None:
                    raise AttributeError("You can't retrieve InstanceOnlyDescriptor.")
                return len(instance.__dict__)

        class MyClass(object):
            x = InstanceOnlyDescriptor()
            y = 13

        # Make sure the 'InstanceOnlyDescriptor' works.
        self.assertRaises(AttributeError, getattr, MyClass, 'x')

        obj = MyClass()
        self.assertEqual(0, obj.x)
        obj.y = 3
        self.assertEqual(1, obj.x)


        # Fetch fields
        fields = dict(utils.iterclass(MyClass))

        # Check for normal fields
        self.assertIn('y', fields)
        self.assertEqual(13, fields['y'])

        # Check that the invalid attribute is ignored.
        self.assertNotIn('x', fields)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
