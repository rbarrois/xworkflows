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

    This exception will be raised when the :attr:`check` parameter of the
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


    .. attribute:: implementation_class

        The class to use when creating :class:`~base.TransitionImplementation` for a :class:`WorkflowEnabled` using this :class:`Workflow`.

        Defaults to :class:`~base.TransitionImplementation`.



Applying workflows
------------------

In order to use a :class:`Workflow`, related objects should inherit from the :class:`WorkflowEnabled` class.


.. class:: WorkflowEnabled

    This class will handle all specific setup related to using :class:`workflows <Workflow>`:

    - Converting ``attr = SomeWorkflow()`` into a :class:`~base.StateProperty` class attribute*
    - Wrapping all :func:`transition`-decorated functions into :class:`~base.TransitionImplementation` wrappers
    - Adding noop implementations for other transitions

    .. attribute:: _workflows

        This class-level attribute holds a dict mapping an attribute to the related :class:`Workflow`.


.. class:: base.WorkflowEnabledMeta

    This metaclass handles the parsing of :class:`WorkflowEnabled` and related magic.



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
all transitions -- initially defined and automatically added -- are replaced with a :class:`base.TransitionImplementation` instance.

.. class:: base.TransitionImplementation

    This class handles applying a :class:`~base.Transition` to a :class:`WorkflowEnabled` object.
    Internally, it acts as a 'non-data descriptor', close to :func:`property`.

    .. attribute:: transition

        The :class:`~base.Transition` performed by this object.

        :type: :class:`~base.Transition`


    .. attribute:: field_name

        The name of the field modified by this :class:`~base.TransitionImplementation` (a string)

        :type: str


    .. attribute:: workflow

        The :class:`Workflow` to which this :class:`~base.TransitionImplementation` relates.

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


.. function:: base.noop(instance)

    The 'do-nothing' function called as default implementation of transitions.


Collecting the :class:`~base.TransitionImplementation`
""""""""""""""""""""""""""""""""""""""""""""""""""""""

.. warning:: This documents private APIs. Use at your own risk.


Building the list of :class:`~base.TransitionImplementation` for a given :class:`WorkflowEnabled`, and generating the missing ones, is a complex job.


.. class:: ImplementationList

    This class performs a few low-level operations on a :class:`WorkflowEnabled` class:

    - Collecting :class:`~base.TransitionWrapper` attributes
    - Converting them into :class:`~base.TransitionImplementation`
    - Adding :func:`~base.noop` implementations for remaining :class:`~base.Transition`
    - Updating the class attributes with those :class:`~base.TransitionImplementation`

    .. attribute:: state_field

        The name of the attribute (from ``attr = SomeWorkflow()`` definition) currently handled.

        :type: :class:`str`

    .. attribute:: _workflow

        The :class:`Workflow` this :class:`~base.ImplementationList` refers to

    .. attribute:: _implems

        Dict mapping an attribute name to the :class:`~base.TransitionImplementation` that should fill it

        :type: :class:`dict` (:class:`str` => :class:`~base.TransitionImplementation`)

    .. attribute:: _transitions_mapping

        Dict mapping the name of a transition to the attribute holding its :class:`~base.TransitionImplementation`::

            @transition('foo')
            def bar(self):
                pass

        will translate into::

            self._implems == {'bar': <function bar at 0xdeadbeed>}
            self._transitions_mapping == {'foo': 'bar'}


    .. method:: collect(self, attrs)

        Collects all :class:`~base.TransitionWrapper` from an attribute dict.

        :raises: ValueError
            If two :class:`~base.TransitionWrapper` for a same :class:`~base.Transition` are defined in the attributes.

    .. method:: _assert_may_override(self, implem, other, attrname)

        Checks whether the :attr:`implem` :class:`~base.TransitionImplementation` is a
        valid override for the :attr:`other` :class:`~base.TransitionImplementation` when
        defined as the :attr:`attrname` class attribute.

        Rules are:

        - A :class:`~base.TransitionImplementation` may not override another :class:`~base.TransitionImplementation` for another :class:`~base.Transition` or another :class:`Workflow`
        - A :class:`~base.TransitionImplementation` may not override a :class:`~base.TransitionWrapper` unless both handle the same :class:`~base.Transition`
        - A :class:`~base.TransitionImplementation` may not override other types of previous definitions,
          unless that previous definition is the wrapped :attr:`~base.TransitionImplementation.implementation`.


    .. method:: update_attrs(self, attrs)

        Adds all :class:`~base.TransitionImplementation` from :attr:`_implems` to the
        given attributes dict.

        Performs the following checks:

        - Makes sure that each :class:`~base.Transition` from the :class:`Workflow` have been
          defined with the :func:`transition` decorator, or that no attributes exists
          with their name

        - If no implementation was defined, adds a :class:`~base.TransitionImplementation` with a :func:`~base.noop` implementation

        - Checks (with :meth:`_assert_may_override`) that the :class:`~base.TransitionImplementation` for the :class:`~base.Transition` is compatible with the existing attributes
