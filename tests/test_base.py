#!/usr/bin/env python
# coding: utf-8

import unittest2

from xworkflows import base


class WorkflowDeclarationTestCase(unittest2.TestCase):
    def test_simple_definition(self):
        class MyWorkflow(base.Workflow):
            states = ('foo', 'bar', 'baz')
            transitions = (
                ('foobar', 'foo', 'bar'),
                ('gobaz', ('foo', 'bar'), 'baz'),
                ('bazbar', 'baz', 'bar'),
            )
            initial_state = 'foo'

        self.assertEqual(3, len(MyWorkflow.states))
        self.assertEqual(3, len(MyWorkflow.transitions))
        self.assertEqual(MyWorkflow.states['foo'], MyWorkflow.initial_state)
        self.assertEqual([MyWorkflow.states['foo']], MyWorkflow.transitions['foobar'].source)
        self.assertEqual(MyWorkflow.states['bar'], MyWorkflow.transitions['foobar'].target)

        for state in MyWorkflow.states:
            self.assertEqual(state.name, state.title)
            self.assertIn(state.name, ('foo', 'bar', 'baz'))

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

        self.assertEqual(3, len(MyWorkflow.states))
        self.assertEqual(3, len(MyWorkflow.transitions))
        self.assertEqual(MyWorkflow.states['foo'], MyWorkflow.initial_state)
        self.assertEqual([MyWorkflow.states['foo']], MyWorkflow.transitions['foobar'].source)
        self.assertEqual(MyWorkflow.states['bar'], MyWorkflow.transitions['foobar'].target)

        for state in MyWorkflow.states:
            self.assertEqual(state.name.capitalize(), state.title)
            self.assertIn(state.name, ('foo', 'bar', 'baz'))


if __name__ == '__main__':
    unittest2.main()
