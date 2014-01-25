XWorkflows
==========

XWorkflows is a library to add workflows, or state machines, to Python objects.

It has been fully tested with all versions of Python from 2.6 to 3.3

Links
-----

* Package on PyPI: http://pypi.python.org/pypi/xworkflows
* Repository and issues on GitHub: http://github.com/rbarrois/xworkflows
* Doc on http://readthedocs.org/docs/xworkflows/

Example
-------

It allows to easilly define a workflow, attach it to a class, and use its transitions::

    import xworkflows

    class MyWorkflow(xworkflows.Workflow):
        # A list of state names
        states = (
            ('foo', "Foo"),
            ('bar', "Bar"),
            ('baz', "Baz"),
        )
        # A list of transition definitions; items are (name, source states, target).
        transitions = (
            ('foobar', 'foo', 'bar'),
            ('gobaz', ('foo', 'bar'), 'baz'),
            ('bazbar', 'baz', 'bar'),
        )
        initial_state = 'foo'


    class MyObject(xworkflows.WorkflowEnabled):
        state = MyWorkflow()

        @xworkflows.transition()
        def foobar(self):
            return 42

        # It is possible to use another method for a given transition.
        @xworkflows.transition('gobaz')
        def blah(self):
            return 13

    >>> o = MyObject()
    >>> o.state
    <StateWrapper: <State: 'foo'>>
    >>> o.state.is_foo
    True
    >>> o.state.name
    'foo'
    >>> o.state.title
    'Foo'
    >>> o.foobar()
    42
    >>> o.state
    <StateWrapper: <State: 'bar'>>
    >>> o.state.name
    'bar'
    >>> o.state.title
    'Bar'
    >>> o.blah()
    13
    >>> o.state
    <StateWrapper: <State: 'baz'>>
    >>> o.state.name
    'baz'
    >>> o.state.title
    'Baz'

Hooks
-----

Custom functions can be hooked to transactions, in order to run before/after a transition,
when entering a state, when leaving a state, ...::


    class MyObject(xworkflows.WorkflowEnabled):

        state = MyWorkflow()

        @xworkflows.before_transition('foobar')
        def my_hook(self, *args, **kwargs):
            # *args and **kwargs are those passed to MyObject.foobar(...)
            pass

        @xworkflows.on_enter_state('bar')
        def my_other_hook(self, result, *args, **kwargs):
            # Will be called just after any transition entering 'bar'
            # result is the value returned by that transition
            # *args, **kwargs are the arguments/keyword arguments passed to the
            # transition.
            pass
