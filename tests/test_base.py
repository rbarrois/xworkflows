#!/usr/bin/env python
# coding: utf-8

import unittest2

from xworkflows import base


class StateTestCase(unittest2.TestCase):

    def test_definition(self):
        self.assertRaises(ValueError, base.State, 'a--b')

    def test_equality(self):
        self.assertNotEqual(base.State('foo', 'Foo'), base.State('foo', 'Foo'))

    def test_repr(self):
        a = base.State('foo', 'Foo')
        self.assertIn('foo', repr(a))
        self.assertIn('Foo', repr(a))


class StateListTestCase(unittest2.TestCase):

    def setUp(self):
        self.foo = base.State('foo', 'Foo')
        self.bar = base.State('bar', 'Bar')
        self.bar2 = base.State('bar', 'Bar')
        self.sl = base.StateList([self.foo, self.bar])

    def test_access(self):
        self.assertEqual(self.foo, self.sl.foo)
        self.assertEqual(self.foo, self.sl['foo'])

        self.assertFalse(hasattr(self.sl, 'baz'))

    def test_contains(self):
        self.assertIn(self.foo, self.sl)
        self.assertIn(self.bar, self.sl)

        self.assertNotIn(self.bar2, self.sl)

    def test_list_methods(self):
        self.assertTrue(self.sl)
        self.assertFalse(base.StateList([]))

        self.assertEqual(2, len(self.sl))


class TransitionDefTestCase(unittest2.TestCase):

    def test_instantiation(self):
        trdef = base.TransitionDef('foobar', 'foo', 'bar')
        self.assertEqual(1, len(trdef.source))
        self.assertEqual(['foo'], trdef.source)

    def test_repr(self):
        trdef = base.TransitionDef('foobar', 'foo', 'bar')
        self.assertIn('foobar', repr(trdef))
        self.assertIn("'foo'", repr(trdef))
        self.assertIn("'bar'", repr(trdef))

    def test_to_transition(self):
        # TODO
        pass

class TransitionListTestCase(unittest2.TestCase):

    def setUp(self):
        self.foo = base.State('foo', 'Foo')
        self.bar = base.State('bar', 'Bar')
        self.baz = base.State('baz', 'Baz')
        self.baz2 = base.State('baz', 'Baz')
        self.foobar = base.Transition('foobar', self.foo, self.bar)
        self.foobar2 = base.Transition('foobar', self.foo, self.bar)
        self.gobaz = base.Transition('gobaz', [self.foo, self.bar], self.baz)
        self.tl = base.TransitionList([self.foobar, self.gobaz])

    def test_access(self):
        self.assertEqual(self.foobar, self.tl.foobar)
        self.assertEqual(self.foobar, self.tl['foobar'])

        self.assertFalse(hasattr(self.tl, 'foobaz'))

    def test_contains(self):
        self.assertIn(self.foobar, self.tl)
        self.assertIn(self.gobaz, self.tl)

        self.assertNotIn(self.foobar2, self.tl)

    def test_list_methods(self):
        self.assertTrue(self.tl)
        self.assertFalse(base.TransitionList([]))

        self.assertEqual(2, len(self.tl))

    def test_available(self):
        self.assertItemsEqual([self.foobar, self.gobaz],
                              list(self.tl.available_from(self.foo)))
        self.assertItemsEqual([self.gobaz],
                              list(self.tl.available_from(self.bar)))
        self.assertEqual([], list(self.tl.available_from(self.baz)))


class StateFieldTestCase(unittest2.TestCase):

    def setUp(self):
        class MyWorkflow(base.Workflow):
            states = ('foo', 'bar', 'baz')
            transitions = (
                ('foobar', 'foo', 'bar'),
                ('gobaz', ('foo', 'bar'), 'baz'),
                ('bazbar', 'baz', 'bar'),
            )
            initial_state = 'foo'

        self.foo = base.State('foo', 'Foo')
        self.bar = base.State('bar', 'Bar')
        self.wf = MyWorkflow
        self.sf = base.StateField(self.foo, self.wf)

    def test_comparison(self):
        self.assertEqual(self.sf, self.foo)
        self.assertEqual(self.foo, self.sf)
        self.assertNotEqual(self.sf, self.bar)
        self.assertNotEqual(self.bar, self.sf)
        self.assertNotEqual(self.sf, 'foo')
        self.assertNotEqual('foo', self.sf)

    def test_attributes(self):
        self.assertTrue(self.sf.is_foo)
        self.assertFalse(self.sf.is_bar)
        self.assertFalse(hasattr(self.sf, 'foo'))
        self.assertEqual(self.foo.name, self.sf.name)
        self.assertEqual(self.foo.title, self.sf.title)


class TransitionImplementationTestCase(unittest2.TestCase):

    def setUp(self):
        self.foo = base.State('foo', 'Foo')
        self.bar = base.State('bar', 'Bar')
        self.baz = base.State('baz', 'Baz')
        self.foobar = base.Transition('foobar', self.foo, self.bar)

    def test_creation(self):
        def blah(obj):
            """doc for blah"""
            pass

        impl = base.TransitionImplementation(self.foobar, 'my_state', blah)

        self.assertIn("'foobar'", repr(impl))
        self.assertIn("blah", repr(impl))
        self.assertIn('my_state', repr(impl))
        self.assertEqual('doc for blah', impl.__doc__)

    def test_using(self):
        def blah(obj):
            pass

        class MyClass(object):
            state = self.foo

        implem = base.TransitionImplementation(self.foobar, 'my_state', blah)

        MyClass.foobar = implem

        self.assertEqual(implem, MyClass.foobar)

        o = MyClass()

        self.assertRaises(TypeError, getattr, o, 'foobar')

    def test_copy(self):
        def blah(obj):
            """docstring for blah"""
            pass

        impl = base.TransitionImplementation(self.foobar, 'my_state', blah)

        copy = impl.copy()
        self.assertEqual(copy.transition, impl.transition)
        self.assertEqual(copy.field_name, impl.field_name)
        self.assertEqual(copy.implementation, impl.implementation)
        self.assertEqual(copy.__doc__, 'docstring for blah')


class TransitionWrapperTestCase(unittest2.TestCase):

    def setUp(self):
        self.wrapper = base.TransitionWrapper('foobar')

    def test_txt(self):
        self.assertIn('foobar', repr(self.wrapper))

    def test_using(self):
        def blah(obj):
            pass

        tr = base.Transition('foobar', base.State('foo'), base.State('bar'))

        res = self.wrapper(blah).get_implem(tr, 'my_state')
        self.assertEqual(tr, res.transition)
        self.assertEqual(blah, res.implementation)
        self.assertEqual('my_state', res.field_name)

    def test_invalid_use(self):
        @self.wrapper
        def blah(obj):
            pass

        tr = base.Transition('foobaz', base.State('foo'), base.State('baz'))

        self.assertRaises(ValueError, self.wrapper.get_implem, tr, 'my_state')



if __name__ == '__main__':
    unittest2.main()
