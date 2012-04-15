#!/usr/bin/env python
# coding: utf-8

import unittest2

from xworkflows import base


class WorkflowDeclarationTestCase(unittest2.TestCase):

    def assertExpected(self, workflow, capitalized_states=True, initial_state='foo'):
        self.assertEqual(3, len(workflow.states))
        self.assertEqual(3, len(workflow.transitions))
        self.assertEqual(workflow.states[initial_state], workflow.initial_state)
        self.assertEqual([workflow.states['foo']], workflow.transitions['foobar'].source)
        self.assertEqual(workflow.states['bar'], workflow.transitions['foobar'].target)

        for state in workflow.states:
            if capitalized_states:
                exp_title = state.name.capitalize()
            else:
                exp_title = state.name
            self.assertEqual(exp_title, state.title)
            self.assertIn(state.name, ('foo', 'bar', 'baz'))


    def test_simple_definition(self):
        class MyWorkflow(base.Workflow):
            states = ('foo', 'bar', 'baz')
            transitions = (
                ('foobar', 'foo', 'bar'),
                ('gobaz', ('foo', 'bar'), 'baz'),
                ('bazbar', 'baz', 'bar'),
            )
            initial_state = 'foo'

        self.assertExpected(MyWorkflow, capitalized_states=False)

    def test_object_definition(self):
        class MyWorkflow(base.Workflow):
            states = (
                base.State('foo', 'Foo'),
                base.State('bar', 'Bar'),
                base.State('baz', 'Baz'),
            )
            transitions = (
                base.TransitionDef('foobar', 'foo', 'bar'),
                base.TransitionDef('gobaz', ('foo', 'bar'), 'baz'),
                base.TransitionDef('bazbar', 'baz', 'bar'),
            )
            initial_state = 'foo'

        self.assertExpected(MyWorkflow)

    def test_alt_simple_definition(self):
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
            states = ('foo', 'bar', 'baz')
            transitions = (
                ('foobar', 'foo', 'bar'),
                ('gobaz', ('foo', 'bar'), 'baz'),
                ('bazbar', 'baz', 'bar'),
            )
            initial_state = 'foo'

        self.assertExpected(MyWorkflow, capitalized_states=False)

        class MySubWorkflow(MyWorkflow):
            initial_state = 'bar'

        self.assertExpected(MySubWorkflow, capitalized_states=False, initial_state='bar')

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
                states = ('foo', 'bar', 'baz')
                transitions = (
                    ('foobar', 'bbb', 'bar'),
                )
                initial_state = 'foo'

        self.assertRaises(KeyError, create_invalid_workflow_3)

        def create_invalid_workflow_4():
            class MyWorkflow(base.Workflow):
                states = ('foo', 'bar', 'baz')
                transitions = (
                    ('foobar', 'bbb'),
                )
                initial_state = 'foo'

        self.assertRaises(TypeError, create_invalid_workflow_4)


class WorkflowEnabledTestCase(unittest2.TestCase):
    def setUp(self):
        class MyWorkflow(base.Workflow):
            states = ('foo', 'bar', 'baz')
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
            states = ('foo', 'bar', 'baz')
            transitions = (
                ('foobar', 'foo', 'bar'),
                ('gobaz', ('foo', 'bar'), 'baz'),
                ('bazbar', 'baz', 'bar'),
            )
            initial_state = 'foo'

            @base.transition('foobar')
            def blah(self):
                pass

        def create_invalid_workflow_enabled():
            class MyWorkflowObject(base.WorkflowEnabled):
                foobar = 42
                wf = MyWorkflow()

        # No implementation for 'foobar' - data from the Workflow was ignored.
        self.assertRaises(ValueError, create_invalid_workflow_enabled)

    def test_override_renamed(self):
        class MyWorkflow(base.Workflow):
            states = ('foo', 'bar', 'baz')
            transitions = (
                ('foobar', 'foo', 'bar'),
                ('gobaz', ('foo', 'bar'), 'baz'),
                ('bazbar', 'baz', 'bar'),
            )
            initial_state = 'foo'

            def foobar(self):
                pass

        class MyWorkflowObject(base.WorkflowEnabled):
            wf = MyWorkflow()

            @base.transition('foobar')
            def blah(self):
                pass

        self.assertFalse(hasattr(MyWorkflowObject, 'foobar'))

    def test_override_conflict(self):
        class MyWorkflow(base.Workflow):
            states = ('foo', 'bar', 'baz')
            transitions = (
                ('foobar', 'foo', 'bar'),
                ('gobaz', ('foo', 'bar'), 'baz'),
                ('bazbar', 'baz', 'bar'),
            )
            initial_state = 'foo'

            def foobar(self):
                pass

        def create_invalid_workflow_enabled():
            class MyWorkflowObject(base.WorkflowEnabled):
                wf = MyWorkflow()

                @base.transition('gobaz')
                def foobar(self):
                    pass

        self.assertRaises(ValueError, create_invalid_workflow_enabled)

    def test_override_with_invalid_wrapper(self):
        class MyWorkflow(base.Workflow):
            states = ('foo', 'bar', 'baz')
            transitions = (
                ('foobar', 'foo', 'bar'),
                ('gobaz', ('foo', 'bar'), 'baz'),
                ('bazbar', 'baz', 'bar'),
            )
            initial_state = 'foo'

            def foobar(self):
                pass

        def create_invalid_workflow_enabled():
            class MyWorkflowObject(base.WorkflowEnabled):
                wf = MyWorkflow()

                @base.transition('blah')
                def foobar(self):
                    pass

        self.assertRaises(ValueError, create_invalid_workflow_enabled)

    def test_override_with_constant(self):
        class MyWorkflow(base.Workflow):
            states = ('foo', 'bar', 'baz')
            transitions = (
                ('foobar', 'foo', 'bar'),
                ('gobaz', ('foo', 'bar'), 'baz'),
                ('bazbar', 'baz', 'bar'),
            )
            initial_state = 'foo'

            def foobar(self):
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
            states = ('foo', 'bar', 'baz')
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


class TransitionRunningTestCase(unittest2.TestCase):

    def setUp(self):
        class MyWorkflow(base.Workflow):
            states = ('foo', 'bar', 'baz')
            transitions = (
                ('foobar', 'foo', 'bar'),
                ('gobaz', ('foo', 'bar'), 'baz'),
                ('bazbar', 'baz', 'bar'),
            )
            initial_state = 'foo'

        class MyWorkflowObject(base.WorkflowEnabled):
            state = MyWorkflow()

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
            states = ('foo', 'bar', 'baz')
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

        # TODO: give the same name to transitions from MyWorkflow and
        # MyAltWorkflow and use decorators to rename them
        self.assertEqual(self.MyWorkflow.states.foo, obj.state1)
        self.assertEqual(MyAltWorkflow.states.foo, obj.state2)


class CustomImplementationTestCase(unittest2.TestCase):

    def setUp(self):
        class MyWorkflow(base.Workflow):
            states = ('foo', 'bar', 'baz')
            transitions = (
                ('foobar', 'foo', 'bar'),
                ('gobaz', ('foo', 'bar'), 'baz'),
                ('bazbar', 'baz', 'bar'),
            )
            initial_state = 'foo'

            def foobar(self, res):
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

            def gobaz(self, res):
                return res + res

        obj = MyWorkflowObject()

        self.assertEqual(self.MyWorkflow.states.foo, obj.state)
        self.assertEqual('blahblah', obj.gobaz('blah'))
        self.assertEqual(self.MyWorkflow.states.baz, obj.state)

    def test_instance_override(self):
        class MyWorkflowObject(base.WorkflowEnabled):
            state = self.MyWorkflow()

            def foobar(self, res):
                return res + res

        obj = MyWorkflowObject()

        self.assertEqual(self.MyWorkflow.states.foo, obj.state)
        self.assertEqual('blahblah', obj.foobar('blah'))
        self.assertEqual(self.MyWorkflow.states.bar, obj.state)

    def test_abort_transition(self):
        class MyWorkflowObject(base.WorkflowEnabled):
            state = self.MyWorkflow()

            def foobar(self):
                raise base.AbortTransitionSilently()

            def gobaz(self):
                raise KeyError()

        obj = MyWorkflowObject()

        self.assertEqual(self.MyWorkflow.states.foo, obj.state)
        self.assertEqual(None, obj.foobar())
        self.assertEqual(self.MyWorkflow.states.foo, obj.state)

        self.assertRaises(KeyError, obj.gobaz)
        self.assertEqual(self.MyWorkflow.states.foo, obj.state)


class ExtendedTransitionImplementationTestCase(unittest2.TestCase):
    """Tests extending TransitionImplementation with extra arguments."""

    def setUp(self):
        class MyWorkflow(base.Workflow):
            states = ('foo', 'bar', 'baz')
            transitions = (
                ('foobar', 'foo', 'bar'),
                ('gobaz', ('foo', 'bar'), 'baz'),
                ('bazbar', 'baz', 'bar'),
            )
            initial_state = 'foo'

        self.MyWorkflow = MyWorkflow

    def test_implementation(self):
        class MyImplementation(base.TransitionImplementation):
            """Custom TransitionImplementation, with extra kwarg 'blah'."""

            def _post_transition(self, instance, res, *args, **kwargs):
                super(MyImplementation, self)._post_transition(instance, res, *args, **kwargs)
                instance.blah = kwargs.get('blah', 42)

        class MyWorkflow(self.MyWorkflow):
            implementation_class = MyImplementation

        class MyWorkflowObject(base.WorkflowEnabled):
            state = MyWorkflow()

            def foobar(self, **kwargs):
                return 1

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


if __name__ == '__main__':
    unittest2.main()
