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

        for state in MyWorkflow.states:
            self.assertEqual(state.name, state.title)
            self.assertIn(state.name, ('foo', 'bar', 'baz'))


if __name__ == '__main__':
    unittest2.main()
