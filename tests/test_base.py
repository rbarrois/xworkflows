#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois
# This code is distributed under the two-clause BSD License.

from .compat import unittest, u

from xworkflows import base


class StateTestCase(unittest.TestCase):

    def test_definition(self):
        self.assertRaises(ValueError, base.State, 'a--b', 'A--B')

    def test_equality(self):
        self.assertNotEqual(base.State('foo', 'Foo'), base.State('foo', 'Foo'))

    def test_repr(self):
        a = base.State('foo', 'Foo')
        self.assertIn('foo', repr(a))
        self.assertNotIn('Foo', repr(a))


class StateListTestCase(unittest.TestCase):

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
        self.assertIn('foo', self.sl)

        self.assertNotIn(self.bar2, self.sl)
        self.assertNotIn('bar2', self.sl)

    def test_list_methods(self):
        self.assertTrue(self.sl)
        self.assertFalse(base.StateList([]))

        self.assertEqual(2, len(self.sl))


class TransitionListTestCase(unittest.TestCase):

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
        self.assertEqual([self.foobar, self.gobaz],
                              list(self.tl.available_from(self.foo)))
        self.assertEqual([self.gobaz],
                              list(self.tl.available_from(self.bar)))
        self.assertEqual([], list(self.tl.available_from(self.baz)))


class StateWrapperTestCase(unittest.TestCase):

    def setUp(self):
        class MyWorkflow(base.Workflow):
            states = (
                ('foo', "Foo"),
                ('bar', "Bar"),
                ('baz', "Baz"),
            )
            transitions = (
                ('foobar', 'foo', 'bar'),
                ('gobaz', ('foo', 'bar'), 'baz'),
                ('bazbar', 'baz', 'bar'),
            )
            initial_state = 'foo'

        self.foo = base.State('foo', 'Foo')
        self.bar = base.State('bar', 'Bar')
        self.wf = MyWorkflow
        self.sf = base.StateWrapper(self.foo, self.wf)
        self.sf2 = base.StateWrapper(self.foo, self.wf)

    def test_comparison(self):
        self.assertEqual(self.sf, self.sf2)
        self.assertEqual(self.sf, self.foo)
        self.assertEqual(self.foo, self.sf)
        self.assertNotEqual(self.sf, self.bar)
        self.assertNotEqual(self.sf, 0)
        self.assertNotEqual(self.bar, self.sf)
        self.assertEqual(self.sf, 'foo')
        self.assertEqual('foo', self.sf)

    def test_attributes(self):
        self.assertTrue(self.sf.is_foo)
        self.assertFalse(self.sf.is_bar)
        self.assertFalse(hasattr(self.sf, 'foo'))
        self.assertEqual(self.foo.name, self.sf.name)
        self.assertEqual(self.foo.title, self.sf.title)

        class BadSubclass(base.StateWrapper):
            def __init__(self, *args, **kwargs):
                self.x = self.state  # Not yet defined!

        self.assertRaises(AttributeError, BadSubclass)

    def test_representation(self):
        self.assertEqual(str(self.foo), str(self.sf))
        self.assertIn(repr(self.foo), repr(self.sf))
        self.assertEqual(self.foo.name, u(self.sf))
        self.assertEqual(hash(self.foo.name), hash(self.sf))


class WorkflowEnabledTestCase(unittest.TestCase):
    def setUp(self):
        super(WorkflowEnabledTestCase, self).setUp()

        class MyWorkflow(base.Workflow):
            states = (
                ('foo', "Foo"),
                ('bar', "Bar"),
                ('baz', "Baz"),
            )
            transitions = (
                ('foobar', 'foo', 'bar'),
                ('gobaz', ('foo', 'bar'), 'baz'),
                ('bazbar', 'baz', 'bar'),
            )
            initial_state = 'foo'

        class MyWorkflowEnabled(base.WorkflowEnabled):
            state = MyWorkflow()

        self.foo = MyWorkflow.states.foo
        self.bar = MyWorkflow.states.bar
        self.wf = MyWorkflow
        self.wfe = MyWorkflowEnabled

    def test_access_state(self):
        obj = self.wfe()
        self.assertEqual(self.foo, obj.state)
        self.assertTrue(obj.state.is_foo)
        self.assertFalse(obj.state.is_bar)

        obj.state = self.bar

        self.assertEqual(self.bar, obj.state)
        self.assertTrue(obj.state.is_bar)
        self.assertFalse(obj.state.is_foo)

    def test_compare_state_text(self):
        obj = self.wfe()

        obj.state = 'bar'

        self.assertEqual(self.bar, obj.state)
        self.assertTrue(obj.state.is_bar)
        self.assertFalse(obj.state.is_foo)


class ImplementationPropertyTestCase(unittest.TestCase):

    def setUp(self):
        self.foo = base.State('foo', 'Foo')
        self.bar = base.State('bar', 'Bar')
        self.baz = base.State('baz', 'Baz')
        self.foobar = base.Transition('foobar', self.foo, self.bar)

    def test_creation(self):
        def blah(obj):  # pragma: no cover
            """doc for blah"""
            pass

        implem = base.ImplementationProperty(
            field_name='my_state', transition=self.foobar, workflow=None,
            implementation=blah)

        self.assertIn("'foobar'", repr(implem))
        self.assertIn("blah", repr(implem))
        self.assertIn('my_state', repr(implem))
        self.assertEqual('doc for blah', implem.__doc__)

    def test_using(self):
        def blah(obj):  # pragma: no cover
            pass

        class MyClass(object):
            state = self.foo

        implem = base.ImplementationProperty(
            field_name='my_state', transition=self.foobar, workflow=None,
            implementation=blah)

        MyClass.foobar = implem
        self.assertEqual(implem, MyClass.foobar)

        o = MyClass()
        self.assertRaises(TypeError, getattr, o, 'foobar')

    def test_copy(self):
        def blah(obj):  # pragma: no cover
            """Doc for blah"""
            pass

        implem = base.ImplementationProperty(
            field_name='my_state', transition=self.foobar, workflow=None,
            implementation=blah)

        implem2 = implem.copy()
        self.assertEqual('my_state', implem2.field_name)
        self.assertEqual(self.foobar, implem2.transition)
        self.assertIsNone(implem2.workflow)
        self.assertEqual(blah, implem2.implementation)
        self.assertEqual("Doc for blah", implem2.__doc__)
        self.assertEqual({}, implem2.hooks)

    def test_copy_exclude_hooks(self):
        def blah(obj):  # pragma: no cover
            """Doc for blah"""
            pass

        @base.before_transition('foo')
        def hook():
            pass

        implem = base.ImplementationProperty(
            field_name='my_state', transition=self.foobar, workflow=None,
            implementation=blah)
        # Structure: {'before': [('foo', hook)]}
        h = hook.xworkflows_hook['before'][0][1]
        implem.add_hook(h)

        implem2 = implem.copy()
        self.assertEqual({}, implem2.hooks)


class TransitionWrapperTestCase(unittest.TestCase):

    def setUp(self):
        self.wrapper = base.TransitionWrapper('foobar')

    def test_txt(self):
        self.assertIn('foobar', repr(self.wrapper))


class HookTestCase(unittest.TestCase):
    def test_validation(self):
        def make_invalid_hook():
            return base.Hook('invalid_kind', base.noop)

        self.assertRaises(AssertionError, make_invalid_hook)

    def test_no_names(self):
        hook = base.Hook(base.HOOK_BEFORE, base.noop)
        self.assertEqual(base.HOOK_BEFORE, hook.kind)
        self.assertEqual(0, hook.priority)
        self.assertEqual(base.noop, hook.function)
        self.assertEqual(('*',), hook.names)

    def test_no_names_but_priority(self):
        hook = base.Hook(base.HOOK_BEFORE, base.noop, priority=42)
        self.assertEqual(base.HOOK_BEFORE, hook.kind)
        self.assertEqual(42, hook.priority)
        self.assertEqual(base.noop, hook.function)
        self.assertEqual(('*',), hook.names)

    def test_some_names_no_priority(self):
        hook = base.Hook(base.HOOK_BEFORE, base.noop, 'foo', 'bar')
        self.assertEqual(base.HOOK_BEFORE, hook.kind)
        self.assertEqual(0, hook.priority)
        self.assertEqual(base.noop, hook.function)
        self.assertEqual(('foo', 'bar'), hook.names)

    def test_some_names_and_priority(self):
        hook = base.Hook(base.HOOK_BEFORE, base.noop, 'foo', 'bar', priority=42)
        self.assertEqual(base.HOOK_BEFORE, hook.kind)
        self.assertEqual(42, hook.priority)
        self.assertEqual(base.noop, hook.function)
        self.assertEqual(('foo', 'bar'), hook.names)

    def test_equality(self):
        hook1 = base.Hook(base.HOOK_BEFORE, base.noop)
        hook2 = base.Hook(base.HOOK_BEFORE, base.noop)
        hook3 = base.Hook(base.HOOK_AFTER, base.noop)
        def alt_noop(*args, **kwargs):  # pragma: no cover
            pass
        hook4 = base.Hook(base.HOOK_BEFORE, alt_noop)
        hook5 = base.Hook(base.HOOK_BEFORE, base.noop, 'foo')
        hook6 = base.Hook(base.HOOK_BEFORE, base.noop, priority=42)

        self.assertEqual(hook1, hook2)
        self.assertNotEqual(hook1, hook3)
        self.assertNotEqual(hook1, hook4)
        self.assertNotEqual(hook1, hook5)
        self.assertNotEqual(hook1, hook6)

    def test_invalid_equality_checks(self):
        hook = base.Hook(base.HOOK_BEFORE, base.noop)
        self.assertTrue(hook != base.noop)
        self.assertFalse(hook == base.noop)

    def test_comparison(self):
        hook1 = base.Hook(base.HOOK_BEFORE, base.noop)
        hook2 = base.Hook(base.HOOK_AFTER, base.noop)
        hook3 = base.Hook(base.HOOK_BEFORE, base.noop, priority=2)
        def alt_noop(*args, **kwargs):  # pragma: no cover
            pass
        hook4 = base.Hook(base.HOOK_BEFORE, alt_noop)

        # Hooks with same priority and function name compare equal wrt cmp
        self.assertFalse(hook1 < hook2)
        self.assertFalse(hook2 < hook1)
        # Hook 3 has higher priority, comes first
        self.assertLess(hook3, hook1)
        # Hook 4 has lower name, comes first
        self.assertLess(hook4, hook1)

    def test_repr(self):
        hook = base.Hook(base.HOOK_BEFORE, base.noop)
        self.assertIn(repr(base.noop), repr(hook))
        self.assertIn(base.HOOK_BEFORE, repr(hook))


class TransitionHookDeclarationTestCase(unittest.TestCase):
    def test_simple_definition(self):
        decl = base.before_transition('foo', 'bar')
        self.assertEqual(0, decl.priority)
        self.assertEqual('', decl.field)
        self.assertEqual(('foo', 'bar'), decl.names)

    def test_definition_no_transition_name(self):
        decl = base.before_transition()
        self.assertEqual(0, decl.priority)
        self.assertEqual('', decl.field)
        self.assertEqual(('*',), decl.names)

    def test_full_definition(self):
        decl = base.before_transition('foo', 'bar', priority=3, field='st')
        self.assertEqual(3, decl.priority)
        self.assertEqual('st', decl.field)
        self.assertEqual(('foo', 'bar'), decl.names)


class StateHookDeclarationTestCase(unittest.TestCase):
    def test_simple_definition(self):
        decl = base.on_enter_state('foo', 'bar')
        self.assertEqual(0, decl.priority)
        self.assertEqual('', decl.field)
        self.assertEqual(('foo', 'bar'), decl.names)

    def test_definition_no_transition_name(self):
        decl = base.on_enter_state()
        self.assertEqual(0, decl.priority)
        self.assertEqual('', decl.field)
        self.assertEqual(('*',), decl.names)

    def test_full_definition(self):
        decl = base.on_enter_state('foo', 'bar', priority=3, field='st')
        self.assertEqual(3, decl.priority)
        self.assertEqual('st', decl.field)
        self.assertEqual(('foo', 'bar'), decl.names)


class ImplementationWrapperTestCase(unittest.TestCase):
    def setUp(self):
        class Dummy(object):
            state1 = 'foo'
            state2 = 'bar'

        self.dummy = Dummy()

    def test_current_state(self):
        wrapper = base.ImplementationWrapper(self.dummy, 'state1', None, None,
            base.noop)
        self.assertEqual('foo', wrapper.current_state)
        self.assertEqual(base.noop.__doc__, wrapper.__doc__)

    def test_repr(self):
        wrapper = base.ImplementationWrapper(self.dummy, 'state1',
            base.Transition('foobar', [base.State('foo', 'Foo')],
                base.State('bar', 'Bar')), None,
            base.noop)
        self.assertIn('foobar', repr(wrapper))
        self.assertIn('state1', repr(wrapper))
        self.assertIn(repr(base.noop), repr(wrapper))


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
