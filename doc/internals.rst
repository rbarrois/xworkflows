=========
Internals
=========

.. module:: xworkflows
    :synopsis: XWorkflows API

This document presents the various classes and components of XWorkflows.

.. note:: All objects defined in the :mod:`base` module should be considered internal API
          and subject to change without notice.

          Refer to ``xworkflows.__init__.py`` to get a list of public objects and methods.

Exceptions
----------

The :mod:`xworkflows` module exposes a few specific exceptions:

.. exception:: WorkflowError

    This is the base for all exceptions from the :mod:`xworkflows` module.

.. exception:: AbortTransition(WorkflowError)

    This error is raised whenever a transition call fails, either due to state
    validation or pre-transition checks.

.. exception:: InvalidTransitionError(AbortTransition)

    This exception is raised when trying to perform a transition from an
    incompatible state.

.. exception:: ForbiddenTransition(AbortTransition)

    This exception will be raised when the :attr:`~base.ImplementationWrapper.check` parameter of the
    :func:`transition` decorator returns a non-``True`` value.


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

A :class:`Workflow` should inherit from the :class:`Workflow` base class, or use the :class:`~base.WorkflowMeta` metaclass
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


    .. attribute:: implementation_class

        The class to use when creating :class:`~base.ImplementationWrapper` for a :class:`WorkflowEnabled` using this :class:`Workflow`.

        Defaults to :class:`~base.ImplementationWrapper`.


.. class:: base.WorkflowMeta

    This metaclass will simply convert the :attr:`~Workflow.states`, :attr:`~Workflow.transitions` and :attr:`~Workflow.initial_state`
    class attributes into the related :class:`~base.StateList`, :class:`~base.TransitionList` and :class:`~base.State` objects.

    During this process, some sanity checks are performed:

    - Each source/target :class:`~base.State` of a :class:`~base.Transition` must appear in
      :attr:`~Workflow.states`
    - The :attr:`~Workflow.initial_state` must appear in :attr:`~Workflow.states`.


Applying workflows
------------------

In order to use a :class:`Workflow`, related objects should inherit from the :class:`WorkflowEnabled` class.


.. class:: WorkflowEnabled

    This class will handle all specific setup related to using :class:`workflows <Workflow>`:

    - Converting ``attr = SomeWorkflow()`` into a :class:`~base.StateProperty` class attribute
    - Wrapping all :func:`transition`-decorated functions into :class:`~base.ImplementationProperty` wrappers
    - Adding noop implementations for other transitions

    .. attribute:: _workflows

        This class-level attribute holds a dict mapping an attribute to the related :class:`Workflow`.


.. class:: base.WorkflowEnabledMeta

    This metaclass handles the parsing of :class:`WorkflowEnabled` and related magic.

    Most of the work is handled by :class:`~base.ImplementationList`, with one instance
    handling each :class:`Workflow` attached to the :class:`WorkflowEnabled` object.



Customizing transitions
-----------------------

A bare :class:`WorkflowEnabled` subclass definition will be automatically modified to
include "noop" implementations for all transitions from related workflows.

In order to customize this behaviour, one should use the :func:`transition` decorator on
methods that should be called when performing transitions.


.. function:: transition([trname='', field='', check=None, before=None, after=None])

    Decorates a method and uses it for a given :class:`~base.Transition`.

    :param str trname: Name of the transition during which the decorated method should be called.
      If empty, the name of the decorated method is used.

    :param str field: Name of the field this transition applies to; useful when two workflows define a transition with the same name.

    :param callable check: An optional function to call before running the transition, with
      the about-to-be-modified instance as single argument.

      Should return ``True`` if the transition can proceed.

    :param callable before: An optional function to call after checks and before the actual
      implementation.

      Receives the same arguments as the transition implementation.

    :param callable after: An optional function to call *after* the transition was performed and logged.

      Receives the instance, the implementation return value and the implementation arguments.


.. class:: base.TransitionWrapper

    Actual class holding all values defined by the :func:`transition` decorator.

    .. attribute:: func

      The decorated function, wrapped with a few checks and calls.


Advanced customization
""""""""""""""""""""""

Once :class:`~base.WorkflowEnabledMeta` has updated the :class:`WorkflowEnabled` subclass,
all transitions -- initially defined and automatically added -- are replaced with a :class:`base.ImplementationProperty` instance.

.. class:: base.ImplementationProperty

    This class holds all objects required to instantiate a :class:`~base.ImplementationWrapper`
    whenever the attribute is accessed on an instance.

    Internally, it acts as a 'non-data descriptor', close to :func:`property`.

    .. method:: __get__(self, instance, owner)

        This method overrides the :func:`getattr` behavior:

        - When called without an instance (``instance=None``), returns itself
        - When called with an instance, this will instantiate a :class:`~base.ImplementationWrapper`
          attached to that instance and return it.


.. class:: base.ImplementationWrapper

    This class handles applying a :class:`~base.Transition` to a :class:`WorkflowEnabled` object.

    .. attribute:: instance

        The :class:`WorkflowEnabled` object to modify when :func:`calling <__call__>` this wrapper.

    .. attribute:: field_name

        The name of the field modified by this :class:`~base.ImplementationProperty` (a string)

        :type: str


    .. attribute:: transition

        The :class:`~base.Transition` performed by this object.

        :type: :class:`~base.Transition`


    .. attribute:: workflow

        The :class:`Workflow` to which this :class:`~base.ImplementationProperty` relates.

        :type: :class:`Workflow`


    .. attribute:: implementation

        The actual method to call when performing the transition. For undefined implementations, uses :func:`~base.noop`.

        :type: callable


    .. attribute:: check

        An optional method to call before calling :attr:`implementation`.
        This method will be called just after :class:`~base.State` checks, and should return ``True`` if the transition is allowed to proceed.

        Will be called with the about-to-update instance.

        :type: callable or :obj:`None`


    .. attribute:: before

        An optional method to call after all checks and just before the :attr:`implementation`.

        Will be called with:

        - The about-to-update instance
        - The ``*args`` used when calling the transition
        - The ``**kwargs`` used when calling the transition

        :type: callable or :obj:`None`


    .. attribute:: after

        An optional method to call after :attr:`implementation`, the :class:`~base.State` change and the :meth:`Workflow.log_transition` call.

        Will be called with:

        - The updated instance
        - The return value of :attr:`implementation`
        - The ``*args`` used when calling the transition
        - The ``**kwargs`` used when calling the transition


    .. method:: __call__

        This method allows the :class:`~base.TransitionWrapper` to act as a function,
        performing the whole range of checks and hooks before and after calling the
        actual :attr:`implementation`.


    .. method:: is_available()

        Determines whether the wrapped transition implementation can be called.
        In details:

        - it makes sure that the current state of the instance is compatible with
          the transition;
        - it calls the :attr:`check` attribute, if defined.

        :rtype: :class:`bool`



.. function:: base.noop(instance)

    The 'do-nothing' function called as default implementation of transitions.


Collecting the :class:`~base.ImplementationProperty`
""""""""""""""""""""""""""""""""""""""""""""""""""""

.. warning:: This documents private APIs. Use at your own risk.


Building the list of :class:`~base.ImplementationProperty` for a given :class:`WorkflowEnabled`, and generating the missing ones, is a complex job.


.. class:: base.ImplementationList

    This class performs a few low-level operations on a :class:`WorkflowEnabled` class:

    - Collecting :class:`~base.TransitionWrapper` attributes
    - Converting them into :class:`~base.ImplementationProperty`
    - Adding :func:`~base.noop` implementations for remaining :class:`~base.Transition`
    - Updating the class attributes with those :class:`~base.ImplementationProperty`

    .. attribute:: state_field

        The name of the attribute (from ``attr = SomeWorkflow()`` definition) currently handled.

        :type: :class:`str`

    .. attribute:: workflow

        The :class:`Workflow` this :class:`~base.ImplementationList` refers to

    .. attribute:: implementations

        Dict mapping a transition name to the related :class:`~base.ImplementationProperty`

        :type: :class:`dict` (:class:`str` => :class:`~base.ImplementationProperty`)

    .. attribute:: transitions_at

        Dict mapping the name of a transition to the attribute holding its :class:`~base.ImplementationProperty`::

            @transition('foo')
            def bar(self):
                pass

        will translate into::

            self.implementations == {'foo': <ImplementationProperty for 'foo' on 'state': <function bar at 0xdeadbeed>>}
            self.transitions_at == {'foo': 'bar'}


    .. method:: should_collect(self, value)

        Whether a given attribute value should be collected in the current list.

        Checks that it is a :class:`~base.TransitionWrapper`, for a :class:`~base.Transition`
        of the current :class:`Workflow`, and relates to the current :attr:`state_field`.


    .. method:: collect(self, attrs)

        Collects all :class:`~base.TransitionWrapper` from an attribute dict if they
        verify :func:`should_collect`.

        :raises: ValueError
            If two :class:`~base.TransitionWrapper` for a same :class:`~base.Transition` are defined in the attributes.


    .. method:: add_missing_implementations(self)

        Registers :func:`~base.noop` :class:`~base.ImplementationProperty` for all
        :class:`~base.Transition` that weren't collected in the :func:`collect` step.


    .. method:: _may_override(self, implem, other)

        Checks whether the :attr:`implem` :class:`~base.ImplementationProperty` is a
        valid override for the :attr:`other` :class:`~base.ImplementationProperty`.

        Rules are:

        - A :class:`~base.ImplementationProperty` may not override another :class:`~base.ImplementationProperty` for another :class:`~base.Transition` or another :attr:`state_field`
        - A :class:`~base.ImplementationProperty` may not override a :class:`~base.TransitionWrapper` unless it was generated from that :class:`~base.TransitionWrapper`
        - A :class:`~base.ImplementationProperty` may not override other types of previous definitions.


    .. method:: fill_attrs(self, attrs)

        Adds all :class:`~base.ImplementationProperty` from :attr:`implementations` to the
        given attributes dict, unless :meth:`_may_override` prevents the operation.


    .. method:: transform(self, attrs, add_missing=True)

        :param dict attrs: Mapping holding attribute declarations from a class definition
        :param add_missing: Whether implementations should be added for transitions
                            without an implementation.

        Performs the following actions, in order:

        - :meth:`collect`: Create :class:`~base.ImplementationProperty` from the
          :class:`transition wrappers <base.TransitionWrapper>` in the :attr:`attrs` dict
        - :meth:`add_missing_implementations`, if :attr:`add_missing` is ``True``:
          create :class:`~base.ImplementationProperty` for the remaining :class:`transitions <base.Transition>`
        - :meth:`fill_attrs`: Update the :attr:`attrs` dict with the
          :class:`implementations <base.ImplementationProperty>` defined in the
          previous steps.

