=========
Reference
=========

.. module:: xworkflows
    :synopsis: XWorkflows API

This document presents the various classes and components of XWorkflows.


States
------

States may be represented with different objects:

- :class:`State` is a basic state (name and title)
- :class:`xworkflows.base.StateWrapper` is an enhanced wrapper around the :class:`State` with enhanced comparison functions.
- :class:`xworkflows.base.StateProperty` is a class-level property-like wrapper around a :class:`State`.

The :class:`State` class
""""""""""""""""""""""""

.. class:: State(name[, title=None])

    This class describes a state in the most simple manner: with an internal name and a human-readable title.

    .. attribute:: name

        The name of the :class:`State`;
        used as an internal representation of the state, this should only contain ascii letters and numbers.

    .. attribute:: title

        The title of the :class:`State`; used for display to users.
        If absent, this is a copy of :attr:`name`.


The :class:`StateWrapper` class
"""""""""""""""""""""""""""""""


.. class:: xworkflows.base.StateWrapper(state, workflow)

    Intended for use as a :class:`WorkflowEnabled` attribute,
    this wraps a :class:`State` with knowledge about the related :class:`Workflow`.

    Its :attr:`__hash__` is computed from the related :attr:`State.name`.
    It compares equal to:

    - Another :class:`~xworkflows.base.StateWrapper` for the same :class:`State`
    - Its :class:`State`
    - The :attr:`~State.name` of its :class:`State`

    .. attribute:: state
    
        The wrapped :class:`State`

    .. attribute:: workflow
    
        The :class:`Workflow` to which this :class:`State` belongs.

    .. method:: transitions()

        :returns: A list of :class:`~xworkflows.base.Transition` with this :class:`State` as source


The :class:`StateProperty` class
""""""""""""""""""""""""""""""""


.. class:: xworkflows.base.StateProperty(workflow, state_field_name)

    Special property-like object (technically a data descriptor), this class controls
    access to the current :class:`State` of a :class:`WorkflowEnabled` object.

    It performs the following actions:

    - Checks that any set value is a valid :class:`State` from the :attr:`workflow` (raises :exc:`ValueError` otherwise)
    - Wraps retrieved values into a :class:`~xworkflows.base.StateWrapper`

    .. attribute:: workflow

        The :class:`Workflow` to which the attribute is related

    .. attribute:: state_field_name

        The name of the attribute wrapped by this :class:`~xworkflows.base.StateProperty`.


Workflows
---------


A :class:`Workflow` definition is slightly different from the resulting class.

A few class-level declarations will be converted into advanced objects:

- :attr:`~Workflow.states` is defined as a list of two-tuples and converted into a :class:`~xworkflows.base.StateList`
- :attr:`~Workflow.transitions` is defined as a list of three-tuples and converted into a :class:`~xworkflows.base.TransitionList`
- :attr:`~Workflow.initial_state` is defined as the :attr:`~State.name` of the initial :class:`State` of the :class:`Workflow` and converted into that :class:`State`


Workflow definition
"""""""""""""""""""

A :class:`Workflow` definition must inherit from the :class:`Workflow` class, or use the :class:`xworkflows.base.WorkflowMeta` metaclass for proper setup.

Defining states
'''''''''''''''

The list of states should be defined as a list of two-tuples of ``(name, title)``::

    class MyWorkflow(xworkflows.Workflow):
        states = (
            ('initial', "Initial"),
            ('middle', "Intermediary"),
            ('final', "Final - all is said and done."),
        )

This is converted into a :class:`~xworkflows.base.StateList` object.

.. class:: xworkflows.base.StateList

    This class acts as a mixed dictionary/object container of :class:`states <State>`::

        >>> MyWorkflow.states.initial
        State('initial')
        >>> MyWorkflow.states['initial']
        State('initial')
        >>> 'initial' in MyWorkflow.states
        True
        >>> list(MyWorkflow.states)  # Definition order is kept
        [State('initial'), State('middle'), State('final')]


Defining transitions
''''''''''''''''''''

At a :class:`Workflow` level, transition are defined in a list of three-tuples:

- transition name
- list of the :attr:`names <State.name>` of source :class:`states <State>` for the transition, or name of the source state if unique
- :attr:`name <State.name>` of the target :class:`State`

.. sourcecode:: python

    class MyWorkflow(xworkflows.Workflow):
        transitions = (
            ('advance', 'initial', 'middle'),
            ('end', ['initial', 'middle'], 'final'),
        )

This is converted into a :class:`~xworkflows.base.TransitionList` object.

.. class:: xworkflows.base.TransitionList

    This acts as a mixed dictionary/object container of :class:`transitions <xworkflows.base.Transition>`::

        >>> MyWorkflow.transitions.advance
        Transition('advance', [State('initial')], State('middle'))
        >>> MyWorkflow.transitions['end']
        Transition('end', [State('initial'), State('middle')], State('final'))
        >>> 'advance' in MyWorkflow.transitions
        True
        >>> MyWorkflow.transitions.available_from(MyWorkflow.states.initial)
        [Transition('advance'), Transition('end')]

    .. method:: available_from(state)

        Retrieve the list of :class:`~xworkflows.base.Transition` available from the given :class:`State`.


.. class:: xworkflows.base.Transition

    Container for a transition.

    .. attribute:: name

        The name of the :class:`~xworkflows.base.Transition`; should be a valid Python identifier

    .. attribute:: source

        A list of source :class:`states <State>` for this :class:`~xworkflows.base.Transition`

    .. attribute:: target

        The target :class:`State` for this :class:`~xworkflows.base.Transition`


Workflow attributes
"""""""""""""""""""

A :class:`Workflow` should inherit from the :class:`Workflow` base class, or use the :class:`WorkflowMeta` metaclass
(that builds the :attr:`~Workflow.states`, :attr:`~Workflow.transitions`, :attr:`~Workflow.initial_state` attributes).

.. class:: Workflow

    This class holds the definition of a workflow.

    .. attribute:: states

        A :class:`~xworkflows.base.StateList` of all :class:`State` for this :class:`Workflow`

    .. attribute:: transitions

        A :class:`~xworkflows.base.TransitionList` of all :class:`~xworkflows.base.Transition` for this :class:`Workflow`

    .. attribute:: initial_state

        The initial :class:`State` for this :class:`Workflow`

    .. method:: log_transition(transition, from_state, instance, *args, **kwargs)

        .. ** [Disable vim syntax]

        :param transition: The :class:`~xworkflows.base.Transition` just performed
        :param from_state: The source :class:`State` of the instance (before performing a transition)
        :param instance: The :class:`object` undergoing a transition
        :param args: All non-keyword arguments passed to the transition implementation
        :param kwargs: All keyword arguments passed to the transition implementation

        This method allows logging all transitions performed by objects using a given workflow.

        The default implementation logs to the logging module, in the ``xworkflows.base`` logger.
