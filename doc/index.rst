.. XWorkflows documentation master file, created by
   sphinx-quickstart on Mon Jun 20 14:00:10 2011.

XWorkflows
==========

XWorkflows is a library designed to bring a simple approach to workflows in Python.

It provides:

- Simple workflow definition
- Running code when performing transitions
- Hooks for running extra code before/after the transition
- A hook for logging performed transitions

You can also refer to the `django_xworkflows <http://github.com/rbarrois/django_xworkflows>`_ project for integration with Django.


Getting started
===============

First, install the `xworkflows <http://pypi.python.org/pypi/xworkflows>`_ package::

    pip install xworkflows


Declaring workflows
-------------------

You can now define a :class:`~xworkflows.Workflow`::

    import xworkflows

    class MyWorkflow(xworkflows.Workflow):
        states = (
            ('init', "Initial state"),
            ('ready', "Ready"),
            ('active', "Active"),
            ('done', "Done"),
            ('cancelled', "Cancelled"),
        )

        transitions = (
            ('prepare', 'init', 'ready'),
            ('activate', 'ready', 'active'),
            ('complete', 'active', 'done'),
            ('cancelled', ('ready', 'active'), 'cancelled'),
        )

        initial_state = 'init'


Applying a workflow
-------------------

In order to apply that workflow to an object, you must:

* Inherit from :class:`xworkflows.WorkflowEnabled`
* Define one (or more) class attributes as :class:`~xworkflows.Workflow` instances.

Here is an example::

    class MyObject(xworkflows.WorkflowEnabled):
        state = MyWorkflow()


Using the transitions
---------------------

With the previous definition, some methods have been *magically* added to your object
definition (have a look at :class:`~xworkflows.base.WorkflowEnabledMeta` to see how).

There is now one method per transition defined in the workflow:

.. sourcecode:: pycon

    >>> obj = MyObject()
    >>> obj.state
    <StateWrapper: <State: 'init'>>
    >>> obj.state.name
    'init'
    >>> obj.state.title
    'Initial state'
    >>> obj.prepare()
    >>> obj.state
    <StateWrapper: <State: 'ready'>>
    >>> obj.state.name
    'ready'
    >>> obj.state.title
    'Ready'


As seen in the example above, calling a transition automatically updates the state
of the workflow.

Only transitions compatible with the current state may be called:

.. sourcecode:: pycon

    >>> obj.state
    <StateWrapper: <State: 'ready'>>
    >>> obj.complete()
    Traceback (most recent call last):
        File "<stdin>", line 1, in <module>
    InvalidTransitionError: Transition 'complete' isn't available from state 'ready'.


Custom transition code
----------------------

It is possible to define explicit code for a transition::

    class MyObject(xworkflows.WorkflowEnabled):
        state = MyWorkflow()

        @xworkflows.transition()
        def activate(self, user):
            self.activated_by = user
            print("State is %s" % self.state.name)

    obj = MyObject()

When calling the transition, the custom code is called before updating the state:

.. sourcecode:: pycon

    >>> obj.state
    <StateWrapper: <State: 'init'>>
    >>> obj.prepare()
    >>> obj.state
    <StateWrapper: <State: 'ready'>>
    >>> obj.activate('blah')
    State is ready
    >>> obj.state
    <StateWrapper: <State: 'active'>>
    >>> obj.activated_by
    'blah'

Hooks
-----

Other functions can be hooked onto transitions, through the :func:`~xworkflows.before_transition`,
:func:`~xworkflows.after_transition`, :func:`~xworkflows.transition_check`,
:func:`~xworkflows.on_enter_state` and :func:`~xworkflows.on_leave_state` decorators::

    class MyObject(xworkflows.WorkflowEnabled):
        state = MyWorkflow()

        @xworkflows.before_transition('foobar', 'gobaz')
        def hook(self, *args, **kwargs):
            pass

Contents
========

.. toctree::
    :maxdepth: 2

    reference
    internals
    changelog

Resources
=========

* Package on PyPI: http://pypi.python.org/pypi/xworkflows
* Repository and issues on GitHub: http://github.com/rbarrois/xworkflows
* Doc on http://readthedocs.org/docs/xworkflows/


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

