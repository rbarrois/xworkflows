Definitions
===========


Workflow definition
-------------------

There are several ways of defining a :class:`Workflow`, but all use a common structure::

    class MyWorkflow(xworkflows.Workflow):
        states = {
            'init': _(u"Initial state"),
            'ready': _(u"Ready"),
            'active': _(u"Active"),
            'done': _(u"Done"),
            'cancelled': _(u"Cancelled"),
        }

        initial_state = 'init'

        transitions = {
            'prepare': ('init', 'ready'),
            'activate': ('ready', 'active'),
            'complete': ('active', 'done'),
            'cancelled': (('ready', 'active'), 'cancelled'),
        }

State list
----------

A state list might be defined in a variety of formats:

* As a tuple of pairs::

    states = (
        ('state_name', 'state_title'),
        ('other_state_name', 'other_state_title'),
    )

* As a dictionary mapping state names to description::

    states = {
        'state_name': 'state_title',
        'other_state_name': 'other_state_title',
    }

* As a list of state names (titles will be deduced directly)::

    states = ['state_name', 'other_state_name']


Transitions
-----------

Transitions might be defined in a variety of formats:

* As a list of triplets::

    transitions = (
        ('transition_name', 'state_from1', 'state_to'),
    )
    transitions = (
        ('transition_name', ('state_from1', 'state_from2'), 'state_to'),
    )

* As a list of dicts::

    transitions = {
        'transition_name': ('state_from1', 'state_to'),
    }
    transitions = {
        'transition_name': (('state_from1', 'state_from2'), 'state_to'),
    }

* As a list of :class:`TransitionDef`::

    transitions = [
        TransitionDef('transition_name', from=['state_from1', 'state_from2'], to='state_to'),
    ]

Initial state
-------------

The initial state is defined as the :attr:`Workflow.initial_state` attribute of the workflow definition::

    initial_state = 'state_name'

Transition function
-------------------

Each transition may have an associated function. This is done through the :func:`transition` decorator::

    class MyWorkflow(Workflow):

        @transition
        def my_transition(self, obj):
