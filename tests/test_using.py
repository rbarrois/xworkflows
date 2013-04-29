#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois
# This code is distributed under the two-clause BSD License.

import warnings

from .compat import is_python3, unittest, u

from xworkflows import base


class WorkflowDeclarationTestCase(unittest.TestCase):

    def assertExpected(self, workflow, initial_state='foo'):
        self.assertEqual(3, len(workflow.states))
        self.assertEqual(3, len(workflow.transitions))
        self.assertEqual(workflow.states[initial_state], workflow.initial_state)
        self.assertEqual([workflow.states['foo']], workflow.transitions['foobar'].source)
        self.assertEqual(workflow.states['bar'], workflow.transitions['foobar'].target)

        for state in workflow.states:
            exp_title = state.name.capitalize()
            self.assertEqual(exp_title, state.title)
            self.assertIn(state.name, ('foo', 'bar', 'baz'))

    def test_simple_definition(self):
        class MyWorkflow(base.Workflow):
            states = (
                ('foo', 'Foo'),
                ('bar', 'Bar'),
                ('baz', 'Baz'),
            )
            transitions = (
                ('foobar', ('foo',), 'bar'),
                ('gobaz', ('foo', 'bar'), 'baz'),
                ('bazbar', ('baz',), 'bar'),
            )
            initial_state = 'foo'

        self.assertExpected(MyWorkflow)

    def test_subclassing(self):
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

        self.assertExpected(MyWorkflow)

        class MySubWorkflow(MyWorkflow):
            initial_state = 'bar'

        self.assertExpected(MySubWorkflow, initial_state='bar')

    def test_subclassing_alt(self):
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

        self.assertExpected(MyWorkflow)

        class MySubWorkflow(MyWorkflow):
            initial_state = 'bar'
            states = (
                ('bar', "BARBAR"),
                ('blah', 'Blah'),
            )
            transitions = (
                ('gobaz', ('foo', 'bar', 'blah'), 'baz'),
                ('blahblah', ('blah',), 'blah'),
            )

        self.assertEqual(4, len(MySubWorkflow.states))
        self.assertEqual([st.name for st in MySubWorkflow.states],
            ['foo', 'bar', 'baz', 'blah'])
        self.assertEqual('bar', MySubWorkflow.initial_state.name)
        self.assertEqual(MySubWorkflow.states.bar, MySubWorkflow.initial_state)
        self.assertEqual('BARBAR', MySubWorkflow.states.bar.title)
        self.assertEqual('Blah', MySubWorkflow.states.blah.title)

        self.assertEqual(4, len(MySubWorkflow.transitions))
        self.assertEqual([tr.name for tr in MySubWorkflow.transitions],
            ['foobar', 'gobaz', 'bazbar', 'blahblah'])
        self.assertEqual(3, len(MySubWorkflow.transitions.gobaz.source))

    def test_invalid_definitions(self):
        def create_invalid_workflow_1():
            class MyWorkflow(base.Workflow):
                states = (12, 13, 14)
                transitions = tuple()
                initial_state = 12

        self.assertRaises(TypeError, create_invalid_workflow_1)

        def create_invalid_workflow_2():
            class MyWorkflow(base.Workflow):
                states = (
                    (1, 2, 3),
                    (2, 3, 4)
                )
                transitions = tuple()
                initial_state = 12

        self.assertRaises(TypeError, create_invalid_workflow_2)

        def create_invalid_workflow_3():
            class MyWorkflow(base.Workflow):
                states = (
                    ('foo', "Foo"),
                    ('bar', "Bar"),
                    ('baz', "Baz"),
                )
                transitions = (
                    ('foobar', 'bbb', 'bar'),
                )
                initial_state = 'foo'

        self.assertRaises(KeyError, create_invalid_workflow_3)

        def create_invalid_workflow_4():
            class MyWorkflow(base.Workflow):
                states = (
                    ('foo', "Foo"),
                    ('bar', "Bar"),
                    ('baz', "Baz"),
                )
                transitions = (
                    ('foobar', 'bbb'),
                )
                initial_state = 'foo'

        self.assertRaises(TypeError, create_invalid_workflow_4)


class WorkflowEnabledTestCase(unittest.TestCase):
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

        self.MyWorkflow = MyWorkflow

    def test_declaration(self):
        class MyWorkflowObject(base.WorkflowEnabled):
            state = self.MyWorkflow()

        self.assertEqual('state', MyWorkflowObject.state.field_name)
        self.assertEqual(self.MyWorkflow.states, MyWorkflowObject.state.workflow.states)
        self.assertIn('state', str(MyWorkflowObject.state))

    def test_instantiation(self):
        class MyWorkflowObject(base.WorkflowEnabled):
            state = self.MyWorkflow()

        obj = MyWorkflowObject()
        self.assertEqual(self.MyWorkflow.initial_state, obj.state)
        self.assertEqual(2, len(list(obj.state.transitions())))

    def test_state_setting(self):
        class MyWorkflowObject(base.WorkflowEnabled):
            state = self.MyWorkflow()

        obj = MyWorkflowObject()

        self.assertRaises(ValueError, setattr, obj, 'state', base.State('a', 'A'))

    def test_implementation_conflict(self):
        def create_invalid_workflow_enabled():
            class MyWorkflowObject(base.WorkflowEnabled):
                wf = self.MyWorkflow()
                foobar = 42

        self.assertRaises(ValueError, create_invalid_workflow_enabled)

    def test_renamed_implementation(self):
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

            @base.transition('foobar')
            def blah(self):  # pragma: no cover
                pass

        def create_invalid_workflow_enabled():
            class MyWorkflowObject(base.WorkflowEnabled):
                foobar = 42
                wf = MyWorkflow()

        # No implementation for 'foobar' - data from the Workflow was ignored.
        self.assertRaises(ValueError, create_invalid_workflow_enabled)

    def test_override_renamed(self):
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

            def foobar(self):  # pragma: no cover
                pass

        class MyWorkflowObject(base.WorkflowEnabled):
            wf = MyWorkflow()

            @base.transition('foobar')
            def blah(self):  # pragma: no cover
                pass

        self.assertFalse(hasattr(MyWorkflowObject, 'foobar'))

    def test_override_conflict(self):
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

            def foobar(self):  # pragma: no cover
                pass

        def create_invalid_workflow_enabled():
            class MyWorkflowObject(base.WorkflowEnabled):
                wf = MyWorkflow()

                @base.transition('gobaz')
                def foobar(self):  # pragma: no cover
                    pass

        self.assertRaises(ValueError, create_invalid_workflow_enabled)

    def test_override_with_invalid_wrapper(self):
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

            def foobar(self):  # pragma: no cover
                pass

        def create_invalid_workflow_enabled():
            class MyWorkflowObject(base.WorkflowEnabled):
                wf = MyWorkflow()

                @base.transition('blah')
                def foobar(self):  # pragma: no cover
                    pass

        self.assertRaises(ValueError, create_invalid_workflow_enabled)

    def test_override_with_constant(self):
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

            def foobar(self):  # pragma: no cover
                pass

        def create_invalid_workflow_enabled():
            class MyWorkflowObject(base.WorkflowEnabled):
                wf = MyWorkflow()

                foobar = 42

        self.assertRaises(ValueError, create_invalid_workflow_enabled)

    def test_dual_workflows_conflict(self):

        def create_invalid_workflow_enabled():
            class MyWorkflowObject(base.WorkflowEnabled):
                state1 = self.MyWorkflow()
                state2 = self.MyWorkflow()

        self.assertRaises(ValueError, create_invalid_workflow_enabled)

    def test_dual_workflows(self):
        class MyAltWorkflow(base.Workflow):
            states = (
                ('foo', "Foo"),
                ('bar', "Bar"),
                ('baz', "Baz"),
            )
            transitions = (
                ('altfoobar', 'foo', 'bar'),
                ('altgobaz', ('foo', 'bar'), 'baz'),
                ('altbazbar', 'baz', 'bar'),
            )
            initial_state = 'foo'

        class MyWorkflowObject(base.WorkflowEnabled):
            state1 = self.MyWorkflow()
            state2 = MyAltWorkflow()

        self.assertEqual('state1', MyWorkflowObject.state1.field_name)
        self.assertEqual('state2', MyWorkflowObject.state2.field_name)

        obj = MyWorkflowObject()

        self.assertEqual(self.MyWorkflow.initial_state, obj.state1)
        self.assertEqual(MyAltWorkflow.initial_state, obj.state2)

    def test_inheritance(self):
        class MyObject(base.WorkflowEnabled):
            state = self.MyWorkflow()

        class MySubObject(MyObject):
            @base.transition()
            def foobar(self):
                return 42

        obj = MySubObject()
        self.assertTrue(hasattr(MySubObject, '_workflows'))
        self.assertIn('state', MySubObject._workflows)
        self.assertEqual(self.MyWorkflow.states.foo, obj.state)
        self.assertEqual(42, obj.foobar())
        self.assertEqual(self.MyWorkflow.states.bar, obj.state)
        obj.gobaz()
        self.assertEqual(self.MyWorkflow.states.baz, obj.state)

    def test_inherited_implementation(self):
        class MyObject(base.WorkflowEnabled):
            state = self.MyWorkflow()

            @base.transition()
            def foobar(self):
                return 42

        class MySubObject(MyObject):
            pass

        obj = MySubObject()
        self.assertTrue(hasattr(MySubObject, '_workflows'))
        self.assertIn('state', MySubObject._workflows)
        self.assertEqual(self.MyWorkflow.states.foo, obj.state)
        self.assertEqual(42, obj.foobar())
        self.assertEqual(self.MyWorkflow.states.bar, obj.state)
        obj.gobaz()
        self.assertEqual(self.MyWorkflow.states.baz, obj.state)

    def test_deeply_inherited_implementation(self):
        class MyObject(base.WorkflowEnabled):
            state = self.MyWorkflow()

            @base.transition()
            def foobar(self):
                return 42

        class MySubObject(MyObject):
            pass

        class MySubSubObject(MySubObject):
            pass

        obj = MySubSubObject()
        self.assertTrue(hasattr(MySubSubObject, '_workflows'))
        self.assertIn('state', MySubSubObject._workflows)
        self.assertEqual(self.MyWorkflow.states.foo, obj.state)
        self.assertEqual(42, obj.foobar())
        self.assertEqual(self.MyWorkflow.states.bar, obj.state)
        obj.gobaz()
        self.assertEqual(self.MyWorkflow.states.baz, obj.state)

    def test_inherited_overridden_implementation(self):
        class MyObject(base.WorkflowEnabled):
            state = self.MyWorkflow()

            @base.transition()
            def foobar(self):  # pragma: no cover
                return 13

        class MySubObject(MyObject):
            @base.transition()
            def foobar(self):
                return 42

        class MySubSubObject(MySubObject):
            pass

        obj = MySubSubObject()
        self.assertTrue(hasattr(MySubSubObject, '_workflows'))
        self.assertIn('state', MySubSubObject._workflows)
        self.assertEqual(self.MyWorkflow.states.foo, obj.state)
        self.assertEqual(42, obj.foobar())
        self.assertEqual(self.MyWorkflow.states.bar, obj.state)
        obj.gobaz()
        self.assertEqual(self.MyWorkflow.states.baz, obj.state)

    def test_inheritance_override_workflow(self):
        class MyAltWorkflow(base.Workflow):
            states = (
                ('fo', "Foo"),
                ('br', "Bar"),
                ('bz', "Baz"),
            )
            transitions = (
                ('altfoobar', 'fo', 'br'),
                ('altgobaz', ('fo', 'br'), 'bz'),
                ('altbazbar', 'bz', 'br'),
            )
            initial_state = 'fo'

        class MyObject(base.WorkflowEnabled):
            state = self.MyWorkflow()

        class MySubObject(MyObject):
            state = MyAltWorkflow()

        self.assertTrue(hasattr(MySubObject, '_workflows'))
        self.assertIn('state', MySubObject._workflows)
        self.assertEqual(MyAltWorkflow,
            MySubObject._workflows['state'].workflow.__class__)
        obj = MySubObject()
        self.assertEqual(MyAltWorkflow.states.fo, obj.state)
        self.assertFalse(hasattr(obj, 'gobar'))


class TransitionRunningTestCase(unittest.TestCase):

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

        class MyWorkflowObject(base.WorkflowEnabled):
            state = MyWorkflow()

            def __repr__(self):
                return u("blé∫")

        self.MyWorkflow = MyWorkflow
        self.MyWorkflowObject = MyWorkflowObject

    def test_transition(self):
        obj = self.MyWorkflowObject()

        self.assertEqual(self.MyWorkflow.states['foo'], obj.state)
        obj.foobar()
        self.assertEqual(self.MyWorkflow.states['bar'], obj.state)
        obj.gobaz()
        self.assertEqual(self.MyWorkflow.states.baz, obj.state)
        obj.bazbar()
        self.assertEqual(self.MyWorkflow.states.bar, obj.state)

    def test_invalid_transition(self):
        obj = self.MyWorkflowObject()

        self.assertRaises(base.InvalidTransitionError, obj.bazbar)

    def test_instance_independance(self):
        obj1 = self.MyWorkflowObject()
        obj2 = self.MyWorkflowObject()

        obj1.foobar()

        self.assertEqual(self.MyWorkflow.states.bar, obj1.state)
        self.assertEqual(self.MyWorkflow.states.foo, obj2.state)

    def test_dual_workflows(self):
        class MyAltWorkflow(base.Workflow):
            states = (
                ('foo', "Foo"),
                ('bar', "Bar"),
                ('baz', "Baz"),
            )
            transitions = (
                ('altfoobar', 'foo', 'bar'),
                ('altgobaz', ('foo', 'bar'), 'baz'),
                ('altbazbar', 'baz', 'bar'),
            )
            initial_state = 'foo'

        class MyWorkflowObject(base.WorkflowEnabled):
            state1 = self.MyWorkflow()
            state2 = MyAltWorkflow()

        obj = MyWorkflowObject()

        self.assertEqual(self.MyWorkflow.states.foo, obj.state1)
        self.assertEqual(MyAltWorkflow.states.foo, obj.state2)

    def test_dual_workflows_conflict(self):
        """Define an object with two workflows and conflicting transitions."""

        class MyAltWorkflow(base.Workflow):
            states = (
                ('foo2', "Foo"),
                ('bar2', "Bar"),
                ('baz2', "Baz"),
            )
            transitions = (
                ('foobar', 'foo2', 'bar2'),
                ('gobaz', ('foo2', 'bar2'), 'baz2'),
                ('bazbar', 'baz2', 'bar2'),
            )
            initial_state = 'foo2'

        def create_invalid_workflow_object():
            class MyWorkflowObject(base.WorkflowEnabled):
                state1 = self.MyWorkflow()
                state2 = MyAltWorkflow()

        self.assertRaises(ValueError, create_invalid_workflow_object)

        def create_other_invalid_workflow_object():
            """Resolve only some transitions."""
            class MyWorkflowObject(base.WorkflowEnabled):
                state1 = self.MyWorkflow()
                state2 = MyAltWorkflow()

                @base.transition('foobar', field='state2')
                def foobar2(self):  # pragma: no cover
                    pass

                @base.transition('gobaz', field='state2')
                def gobaz2(self):  # pragma: no cover
                    pass

        self.assertRaises(ValueError, create_other_invalid_workflow_object)

    def test_dual_workflows_conflict_resolved(self):
        """Define an object with two workflows and renamed transitions."""

        class MyAltWorkflow(base.Workflow):
            states = (
                ('foo2', "Foo"),
                ('bar2', "Bar"),
                ('baz2', "Baz"),
            )
            transitions = (
                ('foobar', 'foo2', 'bar2'),
                ('gobaz', ('foo2', 'bar2'), 'baz2'),
                ('bazbar', 'baz2', 'bar2'),
            )
            initial_state = 'foo2'

        class MyWorkflowObject(base.WorkflowEnabled):
            state1 = self.MyWorkflow()
            state2 = MyAltWorkflow()

            @base.transition('foobar', field='state2')
            def foobar2(self):  # pragma: no cover
                pass

            @base.transition('gobaz', field='state2')
            def gobaz2(self):  # pragma: no cover
                pass

            @base.transition('bazbar', field='state2')
            def bazbar2(self):  # pragma: no cover
                pass

        obj = MyWorkflowObject()
        self.assertEqual(self.MyWorkflow.states.foo, obj.state1)
        self.assertEqual(MyAltWorkflow.states.foo2, obj.state2)

        obj.foobar()
        self.assertEqual(self.MyWorkflow.states.bar, obj.state1)
        self.assertEqual(MyAltWorkflow.states.foo2, obj.state2)

        obj.gobaz2()
        self.assertEqual(self.MyWorkflow.states.bar, obj.state1)
        self.assertEqual(MyAltWorkflow.states.baz2, obj.state2)


class CustomImplementationTestCase(unittest.TestCase):

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
                ('barbaz', 'bar', 'baz'),
            )
            initial_state = 'foo'

            def foobar(self, res):  # pragma: no cover
                return res

        self.MyWorkflow = MyWorkflow

    def test_workflow_defined(self):
        class MyWorkflowObject(base.WorkflowEnabled):
            state = self.MyWorkflow()

        obj = MyWorkflowObject()

        self.assertEqual(self.MyWorkflow.states.foo, obj.state)
        self.assertEqual(None, obj.foobar('blah'))  # Workflow method ignored.
        self.assertEqual(self.MyWorkflow.states.bar, obj.state)

    def test_instance_defined(self):
        class MyWorkflowObject(base.WorkflowEnabled):
            state = self.MyWorkflow()

            @base.transition()
            def gobaz(self, res):
                return res + res

        obj = MyWorkflowObject()

        self.assertEqual(self.MyWorkflow.states.foo, obj.state)
        self.assertEqual('blahblah', obj.gobaz('blah'))
        self.assertEqual(self.MyWorkflow.states.baz, obj.state)

    def test_instance_badly_defined(self):
        """Test misuse of the @transition decorator."""
        def misuse_decorator():
            @base.transition
            def my_transition():  # pragma: no cover
                pass

        self.assertRaises(ValueError, misuse_decorator)

    def test_instance_override(self):
        class MyWorkflowObject(base.WorkflowEnabled):
            state = self.MyWorkflow()

            @base.transition()
            def foobar(self, res):
                return res + res

        obj = MyWorkflowObject()

        self.assertEqual(self.MyWorkflow.states.foo, obj.state)
        self.assertEqual('blahblah', obj.foobar('blah'))
        self.assertEqual(self.MyWorkflow.states.bar, obj.state)

    def test_transition_conflict(self):
        """Test conflict of two implementation for the same transition."""
        def declare_bad_workflow():
            class MyWorkflowObject(base.WorkflowEnabled):
                state = self.MyWorkflow()

                @base.transition('foobar')
                def foobar(self):  # pragma: no cover
                    pass

                @base.transition('foobar')
                def altfoobar(self):  # pragma: no cover
                    pass

        self.assertRaises(ValueError, declare_bad_workflow)

    def test_abort_transition(self):
        class MyWorkflowObject(base.WorkflowEnabled):
            state = self.MyWorkflow()

            def check_foobar(self):
                return False

            @base.transition(check=check_foobar)
            def foobar(self):  # pragma: no cover
                pass

            @base.transition()
            def gobaz(self):
                raise KeyError()

        obj = MyWorkflowObject()

        self.assertEqual(self.MyWorkflow.states.foo, obj.state)
        self.assertRaises(base.ForbiddenTransition, obj.foobar)
        self.assertEqual(self.MyWorkflow.states.foo, obj.state)

        self.assertRaises(KeyError, obj.gobaz)
        self.assertEqual(self.MyWorkflow.states.foo, obj.state)

    def test_checks(self):
        class MyWorkflowObject(base.WorkflowEnabled):
            state = self.MyWorkflow()
            x = 13

            def check_foobar(self):
                return self.x == 42

            @base.transition(check=check_foobar)
            def foobar(self):
                pass

            def check_barbaz(self):
                return False

            @base.transition(check=check_barbaz)
            def barbaz(self):  # pragma: no cover
                pass

        obj = MyWorkflowObject()

        # Not available from state==foo
        self.assertRaises(base.InvalidTransitionError, obj.barbaz)
        self.assertFalse(obj.barbaz.is_available())

        # Transition forbidden by check_foobar
        self.assertEqual(self.MyWorkflow.states.foo, obj.state)
        self.assertRaises(base.ForbiddenTransition, obj.foobar)
        self.assertFalse(obj.foobar.is_available())
        self.assertEqual(self.MyWorkflow.states.foo, obj.state)

        obj.x = 42
        self.assertTrue(obj.foobar.is_available())
        obj.foobar()
        self.assertEqual(self.MyWorkflow.states.bar, obj.state)

        self.assertRaises(base.ForbiddenTransition, obj.barbaz)
        self.assertFalse(obj.barbaz.is_available())


class DeprecatedHookTestCase(unittest.TestCase):
    def test_check_hook(self):
        """Test that using @transition(check=X) raises a warning."""
        with warnings.catch_warnings(record=True) as w:
            __warningregistry__.clear()
            warnings.simplefilter('always')

            @base.transition(check=base.noop)
            def foobar(*args, **kwargs):  # pragma: no cover
                pass

            self.assertEqual(1, len(w))
            self.assertIn('deprecated', str(w[0].message))

    def test_before_hook(self):
        """Test that using @transition(before=X) raises a warning."""
        with warnings.catch_warnings(record=True) as w:
            __warningregistry__.clear()
            warnings.simplefilter('always')

            @base.transition(before=base.noop)
            def foobar(*args, **kwargs):  # pragma: no cover
                pass

            self.assertEqual(1, len(w))
            self.assertIn('deprecated', str(w[0].message))

    def test_after_hook(self):
        """Test that using @transition(after=X) raises a warning."""
        with warnings.catch_warnings(record=True) as w:
            __warningregistry__.clear()
            warnings.simplefilter('always')

            @base.transition(after=base.noop)
            def foobar(*args, **kwargs):  # pragma: no cover
                pass

            self.assertEqual(1, len(w))
            self.assertIn('deprecated', str(w[0].message))


class TransitionHookTestCase(unittest.TestCase):
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

        self.MyWorkflow = MyWorkflow

        class MyWorkflowObject(base.WorkflowEnabled):
            state = self.MyWorkflow()

            def __init__(self, state=None):
                self.hooks = []
                if state:
                    self.state = state

            def seen_hook(self, hook_id):
                self.hooks.append(hook_id)

            @base.before_transition('foobar')
            def hook1(self, *args, **kwargs):
                self.seen_hook(1)

            @base.after_transition('foobar', 'gobaz')
            def hook2(self, *args, **kwargs):
                self.seen_hook(2)

            @base.before_transition('foobar', priority=2)
            @base.after_transition('gobaz', priority=3)
            def hook3(self, *args, **kwargs):
                self.seen_hook(3)
                return True

            @base.transition_check()
            def hook4(self, *args, **kwargs):
                self.seen_hook(4)
                return True

            @base.after_transition('gobaz', priority=1)
            @base.after_transition('bazbar')
            @base.after_transition('gobaz', priority=10)
            @base.transition_check('foobar', priority=1)
            def hook5(self, *args, **kwargs):
                self.seen_hook(5)
                return True

        self.MyWorkflowObject = MyWorkflowObject

    def assert_same_hooks(self, actual, expected, kind):
        """Tests that the 'actual' dict contains expected hooks.

        Matching is performed on (priority, callable, kind) pairs.
        """
        expected_items = sorted(
            ((priority, fun, kind) for (priority, fun) in expected),
            key=lambda t: (t[0], hash(t[1]), t[2]))
        actual_items = sorted(
            ((hook.priority, hook.function, hook.kind) for hook in actual),
            key=lambda t: (t[0], hash(t[1]), t[2]))
        self.assertEqual(list(expected_items), list(actual_items))

    def test_declarations(self):
        obj = self.MyWorkflowObject()
        self.assert_same_hooks(obj.foobar.hooks['check'], [
            (0, obj.hook4.__func__),
            (1, obj.hook5.__func__),
        ], 'check')
        self.assert_same_hooks(obj.foobar.hooks['before'], [
            (0, obj.hook1.__func__),
            (2, obj.hook3.__func__),
        ], 'before')
        self.assert_same_hooks(obj.foobar.hooks['after'], [
            (0, obj.hook2.__func__),
        ], 'after')

        self.assert_same_hooks(obj.gobaz.hooks['check'], [
            (0, obj.hook4.__func__),
        ], 'check')
        self.assert_same_hooks(obj.gobaz.hooks.get('before', []), [
        ], 'before')
        self.assert_same_hooks(obj.gobaz.hooks['after'], [
            (0, obj.hook2.__func__),
            (3, obj.hook3.__func__),
            (1, obj.hook5.__func__),
            (10, obj.hook5.__func__),
        ], 'after')

        self.assert_same_hooks(obj.bazbar.hooks['check'], [
            (0, obj.hook4.__func__),
        ], 'check')
        self.assert_same_hooks(obj.bazbar.hooks['after'], [
            (0, obj.hook5.__func__),
        ], 'after')

    def test_checks(self):
        obj = self.MyWorkflowObject()
        self.assertTrue(obj.foobar.is_available())
        self.assertEqual([5, 4], obj.hooks)

        obj = self.MyWorkflowObject()
        self.assertTrue(obj.gobaz.is_available())
        self.assertEqual([4], obj.hooks)

        obj = self.MyWorkflowObject(state=self.MyWorkflow.states.baz)
        self.assertTrue(obj.bazbar.is_available())
        self.assertEqual([4], obj.hooks)

    def test_transitions_a(self):
        obj = self.MyWorkflowObject()
        obj.foobar()
        # check: 5, 4
        # before: 3, 1
        # after: 2
        self.assertEqual([5, 4, 3, 1, 2], obj.hooks)

    def test_transitions_b(self):
        obj = self.MyWorkflowObject()
        obj.gobaz()
        # check: 4
        # before: -
        # after: 5, 3, 5, 2
        self.assertEqual([4, 5, 3, 5, 2], obj.hooks)

    def test_transitions_c(self):
        obj = self.MyWorkflowObject(state=self.MyWorkflow.states.baz)
        obj.bazbar()
        # check: 4
        # before: -
        # after: 5
        self.assertEqual([4, 5], obj.hooks)

    def test_oldstyle_check(self):
        class MyWorkflowObject(base.WorkflowEnabled):
            state = self.MyWorkflow()

            def __init__(self):
                self.hooks = []

            def seen_hook(self, hook_id):
                self.hooks.append(hook_id)

            def hook(self, *args, **kwargs):
                self.seen_hook(1)
                return True

            @base.transition(check=hook)
            def foobar(self, *args, **kwargs):
                self.seen_hook(2)

        obj = MyWorkflowObject()
        obj.foobar.is_available()
        self.assertEqual([1], obj.hooks)
        obj.foobar()
        self.assertEqual([1, 1, 2], obj.hooks)

    def test_oldstyle_before(self):
        class MyWorkflowObject(base.WorkflowEnabled):
            state = self.MyWorkflow()

            def __init__(self):
                self.hooks = []

            def seen_hook(self, hook_id):
                self.hooks.append(hook_id)

            def hook(self, *args, **kwargs):
                self.seen_hook(1)

            @base.transition(before=hook)
            def foobar(self, *args, **kwargs):
                self.seen_hook(2)

        obj = MyWorkflowObject()
        obj.foobar()
        self.assertEqual([1, 2], obj.hooks)

    def test_oldstyle_after(self):
        class MyWorkflowObject(base.WorkflowEnabled):
            state = self.MyWorkflow()

            def __init__(self):
                self.hooks = []

            def seen_hook(self, hook_id):
                self.hooks.append(hook_id)

            def hook(self, *args, **kwargs):
                self.seen_hook(1)

            @base.transition(after=hook)
            def foobar(self, *args, **kwargs):
                self.seen_hook(2)

        obj = MyWorkflowObject()
        obj.foobar()
        self.assertEqual([2, 1], obj.hooks)

    def test_named_state(self):
        class MyWorkflowObject(base.WorkflowEnabled):
            state = self.MyWorkflow()

            def __init__(self):
                self.args = None
                self.kwargs = None

            @base.before_transition(self.MyWorkflow.transitions.foobar)
            def before(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

        obj = MyWorkflowObject()
        self.assertIsNone(obj.args)
        self.assertIsNone(obj.kwargs)

        obj.foobar(1, 2, 3, a=4, b=5)
        self.assertEqual((1, 2, 3), obj.args)
        self.assertEqual({'a': 4, 'b': 5}, obj.kwargs)


    def test_before_args(self):
        class MyWorkflowObject(base.WorkflowEnabled):
            state = self.MyWorkflow()

            def __init__(self):
                self.args = None
                self.kwargs = None

            @base.before_transition('foobar')
            def before(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

        obj = MyWorkflowObject()
        self.assertIsNone(obj.args)
        self.assertIsNone(obj.kwargs)

        obj.foobar(1, 2, 3, a=4, b=5)
        self.assertEqual((1, 2, 3), obj.args)
        self.assertEqual({'a': 4, 'b': 5}, obj.kwargs)

    def test_check_args(self):
        class MyWorkflowObject(base.WorkflowEnabled):
            state = self.MyWorkflow()

            def __init__(self):
                self.args = None
                self.kwargs = None

            @base.transition_check('foobar')
            def check(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs
                return True

        obj = MyWorkflowObject()
        self.assertIsNone(obj.args)
        self.assertIsNone(obj.kwargs)

        obj.foobar(1, 2, 3, a=4, b=5)
        self.assertEqual((), obj.args)
        self.assertEqual({}, obj.kwargs)

    def test_after_args(self):
        class MyWorkflowObject(base.WorkflowEnabled):
            state = self.MyWorkflow()

            def __init__(self):
                self.args = None
                self.kwargs = None

            @base.after_transition('foobar')
            def after(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

            @base.transition()
            def foobar(self, *args, **kwargs):
                return 42

        obj = MyWorkflowObject()
        self.assertIsNone(obj.args)
        self.assertIsNone(obj.kwargs)

        obj.foobar(1, 2, 3, a=4, b=5)
        self.assertEqual((42, 1, 2, 3), obj.args)
        self.assertEqual({'a': 4, 'b': 5}, obj.kwargs)

    def test_mixed_fields(self):
        """Test hooks in a dual workflow setup."""
        class MyWorkflowObject(base.WorkflowEnabled):
            state1 = self.MyWorkflow()
            state2 = self.MyWorkflow()

            def __init__(self):
                self.hooks = []

            def seen_hook(self, hook_id):
                self.hooks.append(hook_id)

            @base.before_transition()
            def hook1(self, *args, **kwargs):
                self.seen_hook(1)

            @base.before_transition('foobar', field='state1')
            def hook2(self, *args, **kwargs):
                self.seen_hook(2)

            @base.transition('foobar', field='state2')
            def foobar2(self):
                pass

            @base.transition('gobaz', field='state2')
            def gobaz2(self):  # pragma: no cover
                pass

            @base.transition('bazbar', field='state2')
            def bazbar2(self):  # pragma: no cover
                pass

        obj = MyWorkflowObject()
        obj.foobar()
        self.assertEqual([1, 2], obj.hooks)

        obj = MyWorkflowObject()
        obj.foobar2()
        self.assertEqual([1], obj.hooks)


class StateHookTestCase(unittest.TestCase):
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

        self.MyWorkflow = MyWorkflow

        class MyWorkflowObject(base.WorkflowEnabled):
            state = self.MyWorkflow()

            def __init__(self, state=None):
                self.hooks = []
                if state:
                    self.state = state

            def seen_hook(self, hook_id):
                self.hooks.append(hook_id)

            @base.on_leave_state('foo')
            def hook1(self, *args, **kwargs):
                self.seen_hook(1)

            @base.on_enter_state('bar', 'baz')
            def hook2(self, *args, **kwargs):
                self.seen_hook(2)

            @base.on_enter_state('bar', priority=2)
            @base.on_leave_state('bar', priority=3)
            def hook3(self, *args, **kwargs):
                self.seen_hook(3)

            @base.on_leave_state()
            def hook4(self, *args, **kwargs):
                self.seen_hook(4)

        self.MyWorkflowObject = MyWorkflowObject

    def assert_same_hooks(self, actual, expected, kind):
        """Tests that the 'actual' dict contains expected hooks.

        Matching is performed on (priority, callable, kind) pairs.
        """
        expected_items = sorted(
            ((priority, fun, kind) for (priority, fun) in expected),
            key=lambda t: (t[0], hash(t[1]), t[2]))
        actual_items = sorted(
            ((hook.priority, hook.function, hook.kind) for hook in actual),
            key=lambda t: (t[0], hash(t[1]), t[2]))
        self.assertEqual(list(expected_items), list(actual_items))

    def test_declarations(self):
        obj = self.MyWorkflowObject()
        self.assert_same_hooks(obj.foobar.hooks['on_leave'], [
            (0, obj.hook1.__func__),
            (0, obj.hook4.__func__),
        ], 'on_leave')
        self.assert_same_hooks(obj.foobar.hooks['on_enter'], [
            (0, obj.hook2.__func__),
            (2, obj.hook3.__func__),
        ], 'on_enter')

        self.assert_same_hooks(obj.gobaz.hooks['on_leave'], [
            (0, obj.hook1.__func__),
            (3, obj.hook3.__func__),
            (0, obj.hook4.__func__),
        ], 'on_leave')
        self.assert_same_hooks(obj.gobaz.hooks['on_enter'], [
            (0, obj.hook2.__func__),
        ], 'on_enter')

        self.assert_same_hooks(obj.bazbar.hooks['on_leave'], [
            (0, obj.hook4.__func__),
        ], 'on_leave')
        self.assert_same_hooks(obj.bazbar.hooks['on_enter'], [
            (0, obj.hook2.__func__),
            (2, obj.hook3.__func__),
        ], 'on_enter')

    def test_transitions_a(self):
        obj = self.MyWorkflowObject()
        obj.foobar()
        # on_leave: 1, 4
        # on_enter: 3, 2
        self.assertEqual([1, 4, 3, 2], obj.hooks)

    def test_transitions_b(self):
        obj = self.MyWorkflowObject()
        obj.gobaz()
        # on_leave: 1, 4
        # on_enter: 2
        self.assertEqual([1, 4, 2], obj.hooks)

    def test_transitions_c(self):
        obj = self.MyWorkflowObject(state=self.MyWorkflow.states.baz)
        obj.bazbar()
        # on_leave: 4
        # on_enter: 3, 2
        self.assertEqual([4, 3, 2], obj.hooks)


class HookInheritanceTestCase(unittest.TestCase):
    """Tests related to hooks and inherited workflows."""

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

        self.MyWorkflow = MyWorkflow

        class MyWorkflowObject(base.WorkflowEnabled):
            state = self.MyWorkflow()

            def __init__(self):
                self.hooks = []

            def seen_hook(self, hook_id):
                self.hooks.append(hook_id)

            @base.before_transition('foobar')
            def hook1(self, *args, **kwargs):
                self.seen_hook(1)

            @base.after_transition('foobar', 'gobaz')
            def hook2(self, *args, **kwargs):
                self.seen_hook(2)

        self.MyWorkflowObject = MyWorkflowObject

    def test_no_override(self):
        class MySubWorkflowObject(self.MyWorkflowObject):
            pass

        obj = MySubWorkflowObject()
        self.assertEqual(self.MyWorkflow.states.foo, obj.state)
        obj.foobar()
        # check: -
        # before: 1
        # after: 2
        self.assertEqual([1, 2], obj.hooks)

    def test_multiple_inherited(self):
        class WorkflowObject(base.WorkflowEnabled):
            state = self.MyWorkflow()

            def __init__(self):
                self.hooks = []

            def seen_hook(self, hook_id):
                self.hooks.append(hook_id)

            @base.on_leave_state('foo')
            def hook1(self, *args, **kwargs):
                self.seen_hook(1)

        class MyFirstSub(WorkflowObject):
            pass

        class MySecondSub(WorkflowObject):
            pass

        o1 = MyFirstSub()
        self.assertEqual(self.MyWorkflow.states.foo, o1.state)
        o1.foobar()
        # check: -
        # before: 1
        # after: 2
        self.assertEqual([1], o1.hooks)

        o2 = MySecondSub()
        self.assertEqual(self.MyWorkflow.states.foo, o2.state)
        o2.foobar()
        # check: -
        # before: 1
        # after: 2
        self.assertEqual([1], o2.hooks)

    def test_extra_hook(self):
        class MySubWorkflowObject(self.MyWorkflowObject):
            @base.before_transition('foobar')
            def hook3(self, *args, **kwargs):
                self.seen_hook(3)

        obj = MySubWorkflowObject()
        self.assertEqual(self.MyWorkflow.states.foo, obj.state)
        obj.foobar()
        # check: -
        # before: 1, 3
        # after: 2
        self.assertEqual([1, 3, 2], obj.hooks)

    def test_conflict_extend(self):
        """Tests that a hook with a conflicting name replaces parents.."""

        class MySubWorkflowObject(self.MyWorkflowObject):
            @base.before_transition('foobar')
            def hook1(self, *args, **kwargs):
                self.seen_hook(3)

        obj = MySubWorkflowObject()
        self.assertEqual(self.MyWorkflow.states.foo, obj.state)
        obj.foobar()
        # check: -
        # before: 3
        # after: 2
        self.assertEqual([3, 2], obj.hooks)

    def test_multiple_inherited_with_implem(self):
        class WorkflowObject(base.WorkflowEnabled):
            state = self.MyWorkflow()

            def __init__(self):
                self.hooks = []

            def seen_hook(self, hook_id):
                self.hooks.append(hook_id)

            @base.transition()
            def foobar(self, *args, **kwargs):
                pass

            @base.on_leave_state('foo')
            def hook1(self, *args, **kwargs):
                self.seen_hook(1)

        class MyFirstSub(WorkflowObject):
            pass

        class MySecondSub(WorkflowObject):
            pass

        o1 = MyFirstSub()
        self.assertEqual(self.MyWorkflow.states.foo, o1.state)
        o1.foobar()
        # check: -
        # before: 1
        # after: 2
        self.assertEqual([1], o1.hooks)

        o2 = MySecondSub()
        self.assertEqual(self.MyWorkflow.states.foo, o2.state)
        o2.foobar()
        # check: -
        # before: 1
        # after: 2
        self.assertEqual([1], o2.hooks)



class ExtendedTransitionImplementationTestCase(unittest.TestCase):
    """Tests extending TransitionImplementation with extra arguments."""

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

        self.MyWorkflow = MyWorkflow

    def test_implementation(self):
        class MyImplementationWrapper(base.ImplementationWrapper):
            """Custom TransitionImplementation, with extra kwarg 'blah'."""

            def _post_transition(self, res, *args, **kwargs):
                super(MyImplementationWrapper, self)._post_transition(res, *args, **kwargs)
                self.instance.blah = kwargs.get('blah', 42)

        class MyWorkflow(self.MyWorkflow):
            implementation_class = MyImplementationWrapper

        class MyWorkflowObject(base.WorkflowEnabled):
            state = MyWorkflow()

            @base.transition()
            def foobar(self, **kwargs):
                return 1

            @base.transition()
            def gobaz(self, blah=10):
                return blah

        obj = MyWorkflowObject()

        # Transition doesn't know 'blah'
        self.assertEqual(1, obj.foobar())
        self.assertEqual(42, obj.blah)

        # Transition knows 'blah'
        self.assertEqual(13, obj.gobaz(blah=13))
        self.assertEqual(13, obj.blah)

        # Transition knows 'blah', but not provided => different defaults.
        obj = MyWorkflowObject()
        self.assertEqual(10, obj.gobaz())
        self.assertEqual(42, obj.blah)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
