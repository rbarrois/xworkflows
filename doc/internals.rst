=========
Internals
=========

.. module:: xworkflows
    :synopsis: XWorkflows API

This document presents the various classes and components of XWorkflows.


States
------

States may be represented with different objects:

- :class:`base.State` is a basic state (name and title)
- :class:`base.StateWrapper` is an enhanced wrapper around the :class:`~base.State` with enhanced comparison functions.
- :class:`base.StateProperty` is a class-level property-like wrapper around a :class:`~base.State`.

The :class:`~base.State` class
""""""""""""""""""""""""""""""

.. class:: base.State(name[, title=None])

    This class describes a state in the most simple manner: with an internal name and a human-readable title.

    .. attribute:: name

        The name of the :class:`~base.State`;
        used as an internal representation of the state, this should only contain ascii letters and numbers.

    .. attribute:: title

        The title of the :class:`~base.State`; used for display to users.
        If absent, this is a copy of :attr:`name`.


The :class:`StateWrapper` class
"""""""""""""""""""""""""""""""


.. class:: base.StateWrapper(state, workflow)

    Intended for use as a :class:`WorkflowEnabled` attribute,
    this wraps a :class:`~base.State` with knowledge about the related :class:`Workflow`.

    Its :attr:`__hash__` is computed from the related :attr:`~base.State.name`.
    It compares equal to:

    - Another :class:`~base.StateWrapper` for the same :class:`~base.State`
    - Its :class:`~base.State`
    - The :attr:`~base.State.name` of its :class:`~base.State`

    .. attribute:: state
    
        The wrapped :class:`~base.State`

    .. attribute:: workflow
    
        The :class:`Workflow` to which this :class:`~base.State` belongs.

    .. method:: transitions()

        :returns: A list of :class:`~base.Transition` with this :class:`~base.State` as source


The :class:`StateProperty` class
""""""""""""""""""""""""""""""""


.. class:: base.StateProperty(workflow, state_field_name)

    Special property-like object (technically a data descriptor), this class controls
    access to the current :class:`~base.State` of a :class:`WorkflowEnabled` object.

    It performs the following actions:

    - Checks that any set value is a valid :class:`~base.State` from the :attr:`workflow` (raises :exc:`ValueError` otherwise)
    - Wraps retrieved values into a :class:`~base.StateWrapper`

    .. attribute:: workflow

        The :class:`Workflow` to which the attribute is related

    .. attribute:: state_field_name

        The name of the attribute wrapped by this :class:`~base.StateProperty`.


Workflows
---------


A :class:`Workflow` definition is slightly different from the resulting class.

A few class-level declarations will be converted into advanced objects:

- :attr:`~Workflow.states` is defined as a list of two-tuples and converted into a :class:`~base.StateList`
- :attr:`~Workflow.transitions` is defined as a list of three-tuples and converted into a :class:`~base.TransitionList`
- :attr:`~Workflow.initial_state` is defined as the :attr:`~base.State.name` of the initial :class:`~base.State` of the :class:`Workflow` and converted into that :class:`~base.State`


Workflow definition
"""""""""""""""""""

A :class:`Workflow` definition must inherit from the :class:`Workflow` class, or use the :class:`base.WorkflowMeta` metaclass for proper setup.

Defining states
'''''''''''''''

The list of states should be defined as a list of two-tuples of ``(name, title)``::

    class MyWorkflow(xworkflows.Workflow):
        states = (
            ('initial', "Initial"),
            ('middle', "Intermediary"),
            ('final', "Final - all is said and done."),
        )

This is converted into a :class:`~base.StateList` object.

.. class:: base.StateList

    This class acts as a mixed dictionary/object container of :class:`states <base.State>`.

    It replaces the :attr:`~Workflow.states` list from the :class:`Workflow` definition.
    
    .. method:: __len__

      Returns the number of states in the :class:`Workflow`

    .. method:: __getitem__

      Allows retrieving a :class:`~base.State` from its name or from an instance,
      in a dict-like manner

    .. method:: __getattr__

      Allows retrieving a :class:`~base.State` from its name, as an attribute of the :class:`~xworkflows.base.StateList`::

        MyWorkflow.states.initial == MyWorkflow.states['initial']

    .. method:: __iter__

      Iterates over the states, in the order they were defined

    .. method:: __contains__

      Tests whether a :class:`~base.State` instance or its :attr:`~base.State.name`
      belong to the :class:`Workflow`


Defining transitions
''''''''''''''''''''

At a :class:`Workflow` level, transition are defined in a list of three-tuples:

- transition name
- list of the :attr:`names <base.State.name>` of source :class:`states <base.State>` for the transition, or name of the source state if unique
- :attr:`name <base.State.name>` of the target :class:`~base.State`

.. sourcecode:: python

    class MyWorkflow(xworkflows.Workflow):
        transitions = (
            ('advance', 'initial', 'middle'),
            ('end', ['initial', 'middle'], 'final'),
        )

This is converted into a :class:`~base.TransitionList` object.

.. class:: base.TransitionList

    This acts as a mixed dictionary/object container of :class:`transitions <base.Transition>`.

    It replaces the :attr:`~Workflow.transitions` list from the :class:`Workflow` definition.

    .. method:: __len__

      Returns the number of transitions in the :class:`Workflow`

    .. method:: __getitem__

      Allows retrieving a :class:`~base.Transition` from its name or from an instance,
      in a dict-like manner

    .. method:: __getattr__

      Allows retrieving a :class:`~base.Transition` from its name, as an attribute of the :class:`~xworkflows.base.TransitionList`::

        MyWorkflow.transitions.accept == MyWorkflow.transitions['accept']

    .. method:: __iter__

      Iterates over the transitions, in the order they were defined

    .. method:: __contains__

      Tests whether a :class:`~base.Transition` instance or its :attr:`~base.Transition.name`
      belong to the :class:`Workflow`

    .. method:: available_from(state)

        Retrieve the list of :class:`~base.Transition` available from the given :class:`~base.State`.


.. class:: base.Transition

    Container for a transition.

    .. attribute:: name

        The name of the :class:`~base.Transition`; should be a valid Python identifier

    .. attribute:: source

        A list of source :class:`states <base.State>` for this :class:`~base.Transition`

    .. attribute:: target

        The target :class:`~base.State` for this :class:`~base.Transition`


Workflow attributes
"""""""""""""""""""

A :class:`Workflow` should inherit from the :class:`Workflow` base class, or use the :class:`WorkflowMeta` metaclass
(that builds the :attr:`~Workflow.states`, :attr:`~Workflow.transitions`, :attr:`~Workflow.initial_state` attributes).

.. class:: Workflow

    This class holds the definition of a workflow.

    .. attribute:: states

        A :class:`~base.StateList` of all :class:`~base.State` for this :class:`Workflow`

    .. attribute:: transitions

        A :class:`~base.TransitionList` of all :class:`~base.Transition` for this :class:`Workflow`

    .. attribute:: initial_state

        The initial :class:`~base.State` for this :class:`Workflow`

    .. method:: log_transition(transition, from_state, instance, *args, **kwargs)

        .. ** [Disable vim syntax]

        :param transition: The :class:`~base.Transition` just performed
        :param from_state: The source :class:`~base.State` of the instance (before performing a transition)
        :param instance: The :class:`object` undergoing a transition
        :param args: All non-keyword arguments passed to the transition implementation
        :param kwargs: All keyword arguments passed to the transition implementation

        This method allows logging all transitions performed by objects using a given workflow.

        The default implementation logs to the logging module, in the ``base`` logger.
