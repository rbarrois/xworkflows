XWorkflows
==========

XWorkflows is a library to add workflows, or state machines, to Python objects.

It allows to easilly define a workflow, attach it to a class, and use its transitions::

    class MyWorkflow(xworkflows.Workflow):
        # A list of state names
        states = ('foo', 'bar', 'baz')
        # A list of transition definitions; items are (name, source states, target).
        transitions = (
            ('foobar', 'foo', 'bar'),
            ('gobaz', ('foo', 'bar'), 'baz'),
            ('bazbar', 'baz', 'bar'),
        )
        initial_state = 'foo'


    class MyObject(xworkflows.WorkflowEnabled):
        state = MyWorkflow()

        # If a method has the name of a transition, it is used as its implementation.
        def foobar(self):
            return 42

        # It is also possible to use another method for a given transition.
        @transition('gobaz')
        def blah(self):
            return 13

    >>> o = MyObject()
    >>> o.state
    State('foo', 'foo')
    >>> o.state.is_foo
    True

    >>> o.foobar()
    42
    >>> o.state
    State('bar', 'bar')

    >>> o.blah()
    13
    >>> o.state
    State('baz', 'baz')
