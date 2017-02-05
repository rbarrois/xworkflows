# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois
# This code is distributed under the two-clause BSD License.


"""Base components of XWorkflows."""

import functools
import inspect
import logging
import re
import warnings

from .compat import is_callable, is_python3, is_string, u
from . import utils

class WorkflowError(Exception):
    """Base class for errors from the xworkflows module."""


class AbortTransition(WorkflowError):
    """Raised to prevent a transition from proceeding."""


class InvalidTransitionError(AbortTransition):
    """Raised when trying to perform a transition not available from current state."""


class ForbiddenTransition(AbortTransition):
    """Raised when the 'check' hook of a transition was defined and returned False."""


class State(object):
    """A state within a workflow.

    Attributes:
        name (str): the name of the state
        title (str): the human-readable title for the state
    """
    STATE_NAME_RE = re.compile('\w+$')

    def __init__(self, name, title):
        if not self.STATE_NAME_RE.match(name):
            raise ValueError('Invalid state name %s.' % name)
        self.name = name
        self.title = title

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<%s: %r>' % (self.__class__.__name__, self.name)


class StateList(object):
    """A list of states."""
    def __init__(self, states):
        self._states = dict((st.name, st) for st in states)
        self._order = tuple(st.name for st in states)

    def __getattr__(self, name):
        try:
            return self._states[name]
        except KeyError:
            raise AttributeError('StateList %s has no state named %s' % (self, name))

    def __len__(self):
        return len(self._states)

    def __getitem__(self, name_or_state):
        if isinstance(name_or_state, State):
            return self._states[name_or_state.name]
        else:
            return self._states[name_or_state]

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._states)

    def __iter__(self):
        for name in self._order:
            yield self._states[name]

    def __contains__(self, state):
        if isinstance(state, State):
            return state.name in self._states and self._states[state.name] == state
        else:  # Expect a state name
            return state in self._states


class Transition(object):
    """A transition.

    Attributes:
        name (str): the name of the Transition
        source (State list): the 'source' states of the transition
        target (State): the 'target' state of the transition
    """
    def __init__(self, name, source, target):
        self.name = name
        if isinstance(source, State):
            source = [source]
        self.source = source
        self.target = target

    def __repr__(self):
        return '%s(%r, %r, %r)' % (self.__class__.__name__,
                                   self.name, self.source, self.target)


class TransitionList(object):
    """Holder for the transitions of a given workflow."""

    def __init__(self, transitions):
        """Create a TransitionList.

        Args:
            transitions (list of (name, source, target) tuple): the transitions
                to include.
        """
        self._transitions = {}
        self._order = []
        for trdef in transitions:
            self._transitions[trdef.name] = trdef
            self._order.append(trdef.name)

    def __len__(self):
        return len(self._transitions)

    def __getattr__(self, name):
        try:
            return self._transitions[name]
        except KeyError:
            raise AttributeError('TransitionList %s has no transition named %s.'
                    % (self, name))

    def __getitem__(self, name):
        return self._transitions[name]

    def __iter__(self):
        for name in self._order:
            yield self._transitions[name]

    def __contains__(self, value):
        if isinstance(value, Transition):
            return value.name in self._transitions and self._transitions[value.name] == value
        else:
            return value in self._transitions

    def available_from(self, state):
        """Retrieve all transitions available from a given state.

        Args:
            state (State): the initial state.

        Yields:
            Transition: all transitions starting from that state
        """
        for transition in self:
            if state in transition.source:
                yield transition

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._transitions.values())


def _setup_states(state_definitions, prev=()):
    """Create a StateList object from a 'states' Workflow attribute."""
    states = list(prev)
    for state_def in state_definitions:
        if len(state_def) != 2:
            raise TypeError("The 'state' attribute of a workflow should be "
                "a two-tuple of strings; got %r instead." % (state_def,))
        name, title = state_def
        state = State(name, title)
        if any(st.name == name for st in states):
            # Replacing an existing state
            states = [state if st.name == name else st for st in states]
        else:
            states.append(state)
    return StateList(states)


def _setup_transitions(tdef, states, prev=()):
    """Create a TransitionList object from a 'transitions' Workflow attribute.

    Args:
        tdef: list of transition definitions
        states (StateList): already parsed state definitions.
        prev (TransitionList): transition definitions from a parent.

    Returns:
        TransitionList: the list of transitions defined in the 'tdef' argument.
    """
    trs = list(prev)
    for transition in tdef:
        if len(transition) == 3:
            (name, source, target) = transition
            if is_string(source) or isinstance(source, State):
                source = [source]
            source = [states[src] for src in source]
            target = states[target]
            tr = Transition(name, source, target)
        else:
            raise TypeError("Elements of the 'transition' attribute of a "
                "workflow should be three-tuples; got %r instead." % (transition,))

        if any(prev_tr.name == tr.name for prev_tr in trs):
            # Replacing an existing state
            trs = [tr if prev_tr.name == tr.name else prev_tr for prev_tr in trs]
        else:
            trs.append(tr)
    return TransitionList(trs)


HOOK_BEFORE = 'before'
HOOK_AFTER = 'after'
HOOK_CHECK = 'check'
HOOK_ON_ENTER = 'on_enter'
HOOK_ON_LEAVE = 'on_leave'


class Hook(object):
    """A hook to run when a transition occurs.

    Attributes:
        kind (str): the kind of hook
        priority (int): the priority of the hook (higher values run first)
        function (callable): the actual function to call
        names (str list): name of the transitions or states to which the hook
            relates. The special value '*' means 'applies to all transitions/
            states'.

    Hooks are sortable by descending priority and ascending function name.

    Hook kinds are as follow:
        - HOOK_BEFORE: run before the related transitions
        - HOOK_AFTER: run after the related transitions
        - HOOK_CHECK: run as part of pre-transition checks (return value matters)
        - HOOK_ON_ENTER: run just after a transition entering a related state
        - HOOK_ON_LEAVE: run just before a transition leaving from a related state
    """

    def __init__(self, kind, function, *names, **kwargs):
        assert kind in (HOOK_BEFORE, HOOK_AFTER, HOOK_CHECK,
            HOOK_ON_ENTER, HOOK_ON_LEAVE)

        self.kind = kind
        self.priority = kwargs.get('priority', 0)
        self.function = function
        self.names = names or ('*',)

    def _match_state(self, state):
        """Checks whether a given State matches self.names."""
        return (self.names == '*'
                or state in self.names
                or state.name in self.names)

    def _match_transition(self, transition):
        """Checks whether a given Transition matches self.names."""
        return (self.names == '*'
                or transition in self.names
                or transition.name in self.names)

    def applies_to(self, transition, from_state=None):
        """Whether this hook applies to the given transition/state.

        Args:
            transition (Transition): the transition to check
            from_state (State or None): the state to check. If absent, the check
                is 'might this hook apply to the related transition, given a
                valid source state'.
        """
        if '*' in self.names:
            return True
        elif self.kind in (HOOK_BEFORE, HOOK_AFTER, HOOK_CHECK):
            return self._match_transition(transition)
        elif self.kind == HOOK_ON_ENTER:
            return self._match_state(transition.target)
        elif from_state is None:
            # Testing whether the hook may apply to at least one source of the
            # transition
            return any(self._match_state(src) for src in transition.source)
        else:
            return self._match_state(from_state)

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)

    def __eq__(self, other):
        """Equality is based on priority, function and kind."""
        if not isinstance(other, Hook):
            return NotImplemented
        return (self.priority == other.priority
            and self.function == other.function
            and self.kind == other.kind
            and self.names == other.names
        )

    def __ne__(self, other):
        if not isinstance(other, Hook):
            return NotImplemented
        return not (self == other)

    def __lt__(self, other):
        """Compare hooks of the same kind."""
        if not isinstance(other, Hook):
            return NotImplemented
        return (
            (other.priority, self.function.__name__)
            < (self.priority, other.function.__name__))

    def __gt__(self, other):
        """Compare hooks of the same kind."""
        if not isinstance(other, Hook):
            return NotImplemented
        return (
            (other.priority, self.function.__name__)
            > (self.priority, other.function.__name__))

    def __repr__(self):
        return '<%s: %s %r>' % (
            self.__class__.__name__, self.kind, self.function)


class ImplementationWrapper(object):
    """Wraps a transition implementation.

    Emulates a function behaviour, but provides a few extra features.

    Attributes:
        instance (WorkflowEnabled): the instance to update
.
        field_name (str): the name of the field of the instance to update.
        transition (Transition): the transition to perform
        workflow (Workflow): the workflow to which this is related.

        hooks (Hook list): optional hooks to call during the transition
        implementation (callable): the code to invoke between 'before' and the
            state update.
    """

    def __init__(self, instance, field_name, transition, workflow,
            implementation, hooks=None):
        self.instance = instance
        self.field_name = field_name
        self.transition = transition
        self.workflow = workflow

        self.hooks = hooks or {}
        self.implementation = implementation

        self.__doc__ = implementation.__doc__

    @property
    def current_state(self):
        return getattr(self.instance, self.field_name)

    def _pre_transition_checks(self):
        """Run the pre-transition checks."""
        current_state = getattr(self.instance, self.field_name)
        if current_state not in self.transition.source:
            raise InvalidTransitionError(
                "Transition '%s' isn't available from state '%s'." %
                (self.transition.name, current_state.name))

        for check in self._filter_hooks(HOOK_CHECK):
            if not check(self.instance):
                raise ForbiddenTransition(
                    "Transition '%s' was forbidden by "
                    "custom pre-transition check." % self.transition.name)

    def _filter_hooks(self, *hook_kinds):
        """Filter a list of hooks, keeping only applicable ones."""
        hooks = sum((self.hooks.get(kind, []) for kind in hook_kinds), [])
        return sorted(hook for hook in hooks
                      if hook.applies_to(self.transition, self.current_state))

    def _pre_transition(self, *args, **kwargs):
        for hook in self._filter_hooks(HOOK_BEFORE, HOOK_ON_LEAVE):
            hook(self.instance, *args, **kwargs)

    def _during_transition(self, *args, **kwargs):
        return self.implementation(self.instance, *args, **kwargs)

    def _log_transition(self, from_state, *args, **kwargs):
        self.workflow.log_transition(self.transition, from_state, self.instance,
            *args, **kwargs)

    def _post_transition(self, result, *args, **kwargs):
        """Performs post-transition actions."""
        for hook in self._filter_hooks(HOOK_AFTER, HOOK_ON_ENTER):
            hook(self.instance, result, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        """Run the transition, with all checks."""

        self._pre_transition_checks()
        # Call hooks.
        self._pre_transition(*args, **kwargs)

        result = self._during_transition(*args, **kwargs)

        from_state = getattr(self.instance, self.field_name)
        setattr(self.instance, self.field_name, self.transition.target)

        # Call hooks.
        self._log_transition(from_state, *args, **kwargs)
        self._post_transition(result, *args, **kwargs)
        return result

    def is_available(self):
        """Check whether this transition is available on the current object.

        Returns:
            bool
        """
        try:
            self._pre_transition_checks()
        except (InvalidTransitionError, ForbiddenTransition):
            return False
        return True

    def __repr__(self):
        return "<%s for %r on %r: %r>" % (self.__class__.__name__,
            self.transition.name, self.field_name, self.implementation)


class ImplementationProperty(object):
    """Holds an implementation of a transition.

    This class is a 'non-data descriptor', somewhat similar to a property.

    Attributes:
        field_name (str): the name of the field of the instance to update.
        transition (Transition): the transition to perform
        workflow (Workflow): the workflow to which this is related.

        hooks (Hook list): hooks to apply along with the transition.
        implementation (callable): the code to invoke between 'before' and the
            state update.
    """
    def __init__(self, field_name, transition, workflow, implementation,
            hooks=None):
        self.field_name = field_name
        self.transition = transition
        self.workflow = workflow
        self.hooks = hooks or {}
        self.implementation = implementation
        self.__doc__ = implementation.__doc__

    def copy(self):
        return self.__class__(
            field_name=self.field_name,
            transition=self.transition,
            workflow=self.workflow,
            implementation=self.implementation,
            # Don't copy hooks: they'll be re-generated during metaclass __new__
            hooks={},
        )

    def add_hook(self, hook):
        self.hooks.setdefault(hook.kind, []).append(hook)

    def __get__(self, instance, owner):
        if instance is None:
            return self

        if not isinstance(instance, BaseWorkflowEnabled):
            raise TypeError(
                "Unable to apply transition '%s' to object %r, which is not "
                "attached to a Workflow." % (self.transition.name, instance))

        return self.workflow.implementation_class(instance,
            self.field_name, self.transition, self.workflow,
            self.implementation, self.hooks)

    def __repr__(self):
        return "<%s for '%s' on '%s': %s>" % (self.__class__.__name__,
            self.transition.name, self.field_name, self.implementation)


class TransitionWrapper(object):
    """Mark that a method should be used for a transition with a different name.

    Attributes:
        trname (str): the name of the transition that the method implements
        func (function): the decorated method
    """

    def __init__(self, trname, field='', check=None, before=None, after=None):
        self.trname = trname
        self.field = field
        self.check = check
        self.before = before
        self.after = after
        self.func = None

    def __call__(self, func):
        self.func = func
        if self.trname == '':
            self.trname = func.__name__
        return self

    def __repr__(self):
        return "<%s for %r: %s>" % (self.__class__.__name__, self.trname, self.func)


def transition(trname='', field='', check=None, before=None, after=None):
    """Decorator to declare a function as a transition implementation."""
    if is_callable(trname):
        raise ValueError("The @transition decorator should be called as "
            "@transition(['transition_name'], **kwargs)")
    if check or before or after:
        warnings.warn(
            "The use of check=, before= and after= in @transition decorators is "
            "deprecated in favor of @transition_check, @before_transition and "
            "@after_transition decorators.",
            DeprecationWarning,
            stacklevel=2)
    return TransitionWrapper(trname, field=field,
        check=check, before=before, after=after)


def _make_hook_dict(fun):
    """Ensure the given function has a xworkflows_hook attribute.

    That attribute has the following structure:
    >>> {
    ...     'before': [('state', <TransitionHook>), ...],
    ... }
    """
    if not hasattr(fun, 'xworkflows_hook'):
        fun.xworkflows_hook = {
            HOOK_BEFORE: [],
            HOOK_AFTER: [],
            HOOK_CHECK: [],
            HOOK_ON_ENTER: [],
            HOOK_ON_LEAVE: [],
        }
    return fun.xworkflows_hook


class _HookDeclaration(object):
    """Base class for decorators declaring methods as transition hooks.

    Args:
        *names (str tuple): name of the states/transitions to bind to; use '*'
            for 'all'
        priority (int): priority of the hook, defaults to 0
        field (str): name of the field to which the hooked transition relates

    Usage:
        >>> @_HookDeclaration('foo', 'bar', priority=4)
        ... def my_hook(self):
        ...   pass
    """

    def __init__(self, *names, **kwargs):
        if not names:
            names = ('*',)
        self.names = names
        self.priority = kwargs.get('priority', 0)
        self.field = kwargs.get('field', '')

    def _as_hook(self, func):
        return Hook(self.hook_name, func, *self.names, priority=self.priority)

    def __call__(self, func):
        hook_dict = _make_hook_dict(func)
        hooks = hook_dict[self.hook_name]
        hooks.append((self.field, self._as_hook(func)))
        return func


class before_transition(_HookDeclaration):
    """Decorates a method that should be called before a given transition.

    Example:
        >>> @before_transition('foobar')
        ... def blah(self):
        ...   pass
    """
    hook_name = HOOK_BEFORE


class after_transition(_HookDeclaration):
    """Decorates a method that should be called after a given transition.

    Example:
        >>> @after_transition('foobar')
        ... def blah(self):
        ...   pass
    """
    hook_name = HOOK_AFTER


class transition_check(_HookDeclaration):
    """Decorates a method that should be called after a given transition.

    Example:
        >>> @transition_check('foobar')
        ... def blah(self):
        ...   pass
    """
    hook_name = HOOK_CHECK


class on_enter_state(_HookDeclaration):
    """Decorates a method that should be used as a hook for a state.

    Example:
        >>> @on_enter_state('foo', 'bar')
        ... def blah(self):
        ...   pass
    """
    hook_name = HOOK_ON_ENTER


class on_leave_state(_HookDeclaration):
    """Decorates a method that should be used as a hook for a state.

    Example:
        >>> @on_leave_state('foo', 'bar')
        ... def blah(self):
        ...   pass
    """
    hook_name = HOOK_ON_LEAVE


def noop(instance, *args, **kwargs):
    """NoOp function, ignores all arguments."""
    pass


class ImplementationList(object):
    """Stores all implementations.

    Attributes:
        state_field (str): the name of the field holding the state of objects.
        implementations (dict(str => ImplementationProperty)): maps a transition
            name to the associated implementation.
        workflow (Workflow): the related workflow
        transitions_at (dict(str => str)): maps a transition name to the
            name of the attribute holding the related implementation.
        custom_implems (str set): list of transition names for which a custom
            implementation has been defined.
    """

    def __init__(self, state_field, workflow):
        self.state_field = state_field
        self.workflow = workflow
        self.implementations = {}
        self.transitions_at = {}
        self.custom_implems = set()

    def load_parent_implems(self, parent_implems):
        """Import previously defined implementations.

        Args:
            parent_implems (ImplementationList): List of implementations defined
                in a parent class.
        """
        for trname, attr, implem in parent_implems.get_custom_implementations():
            self.implementations[trname] = implem.copy()
            self.transitions_at[trname] = attr
            self.custom_implems.add(trname)

    def add_implem(self, transition, attribute, function, **kwargs):
        """Add an implementation.

        Args:
            transition (Transition): the transition for which the implementation
                is added
            attribute (str): the name of the attribute where the implementation
                will be available
            function (callable): the actual implementation function
            **kwargs: extra arguments for the related ImplementationProperty.
        """
        implem = ImplementationProperty(
            field_name=self.state_field,
            transition=transition,
            workflow=self.workflow,
            implementation=function,
            **kwargs)
        self.implementations[transition.name] = implem
        self.transitions_at[transition.name] = attribute
        return implem

    def should_collect(self, value):
        """Decide whether a given value should be collected."""
        return (
            # decorated with @transition
            isinstance(value, TransitionWrapper)
            # Relates to a compatible transition
            and value.trname in self.workflow.transitions
            # Either not bound to a state field or bound to the current one
            and (not value.field or value.field == self.state_field))

    def collect(self, attrs):
        """Collect the implementations from a given attributes dict."""

        for name, value in attrs.items():
            if self.should_collect(value):
                transition = self.workflow.transitions[value.trname]

                if (value.trname in self.implementations
                    and value.trname in self.custom_implems
                    and name != self.transitions_at[value.trname]):
                    # We already have an implementation registered.
                    other_implem_at = self.transitions_at[value.trname]
                    raise ValueError(
                        "Error for attribute %s: it defines implementation "
                        "%s for transition %s, which is already implemented "
                        "at %s." % (name, value, transition, other_implem_at))

                implem = self.add_implem(transition, name, value.func)
                self.custom_implems.add(transition.name)
                if value.check:
                    implem.add_hook(Hook(HOOK_CHECK, value.check))
                if value.before:
                    implem.add_hook(Hook(HOOK_BEFORE, value.before))
                if value.after:
                    implem.add_hook(Hook(HOOK_AFTER, value.after))

    def get_custom_implementations(self):
        """Retrieve a list of cutom implementations.

        Yields:
            (str, str, ImplementationProperty) tuples: The name of the attribute
                an implementation lives at, the name of the related transition,
                and the related implementation.
        """
        for trname in self.custom_implems:
            attr = self.transitions_at[trname]
            implem = self.implementations[trname]
            yield (trname, attr, implem)

    def add_missing_implementations(self):
        for transition in self.workflow.transitions:
            if transition.name not in self.implementations:
                self.add_implem(transition, transition.name, noop)

    def register_hooks(self, cls):
        for field, value in utils.iterclass(cls):
            if is_callable(value) and hasattr(value, 'xworkflows_hook'):
                self.register_function_hooks(value)

    def register_function_hooks(self, func):
        """Looks at an object method and registers it for relevent transitions."""
        for hook_kind, hooks in func.xworkflows_hook.items():
            for field_name, hook in hooks:
                if field_name and field_name != self.state_field:
                    continue
                for transition in self.workflow.transitions:
                    if hook.applies_to(transition):
                        implem = self.implementations[transition.name]
                        implem.add_hook(hook)

    def _may_override(self, implem, other):
        """Checks whether an ImplementationProperty may override an attribute."""
        if isinstance(other, ImplementationProperty):
            # Overriding another custom implementation for the same transition
            # and field
            return (other.transition == implem.transition
                and other.field_name == self.state_field)

        elif isinstance(other, TransitionWrapper):
            # Overriding the definition that led to adding the current
            # ImplementationProperty.
            return (other.trname == implem.transition.name
                and (not other.field or other.field == self.state_field)
                and other.func == implem.implementation)

        return False

    def fill_attrs(self, attrs):
        """Update the 'attrs' dict with generated ImplementationProperty."""
        for trname, attrname in self.transitions_at.items():

            implem = self.implementations[trname]

            if attrname in attrs:
                conflicting = attrs[attrname]
                if not self._may_override(implem, conflicting):
                    raise ValueError(
                        "Can't override transition implementation %s=%r with %r" %
                        (attrname, conflicting, implem))

            attrs[attrname] = implem
        return attrs

    def transform(self, attrs):
        """Perform all actions on a given attribute dict."""
        self.collect(attrs)
        self.add_missing_implementations()
        self.fill_attrs(attrs)


class WorkflowMeta(type):
    """Base metaclass for all Workflows.

    Sets the 'states', 'transitions', and 'initial_state' attributes.
    """

    def __new__(mcs, name, bases, attrs):

        state_defs = attrs.pop('states', [])
        transitions_defs = attrs.pop('transitions', [])
        initial_state = attrs.pop('initial_state', None)

        new_class = super(WorkflowMeta, mcs).__new__(mcs, name, bases, attrs)

        new_class.states = _setup_states(state_defs,
            getattr(new_class, 'states', []))
        new_class.transitions = _setup_transitions(transitions_defs,
            new_class.states, getattr(new_class, 'transitions', []))
        if initial_state is not None:
            new_class.initial_state = new_class.states[initial_state]

        return new_class


class BaseWorkflow(object):
    """Base class for all workflows.

    Attributes:
        states (StateList): list of states of this Workflow
        transitions (TransitionList): list of Transitions of this Workflow
        initial_state (State): initial state for the Workflow
        implementation_class (ImplementationWrapper subclass): class to use
            for transition implementation wrapping.

    For each transition, a ImplementationWrapper with the same name (unless
    another name has been specified through the use of the @transition
    decorator) is provided to perform the specified transition.
    """
    implementation_class = ImplementationWrapper

    def log_transition(self, transition, from_state, instance, *args, **kwargs):
        """Log a transition.

        Args:
            transition (Transition): the name of the performed transition
            from_state (State): the source state
            instance (object): the modified object

        Kwargs:
            Any passed when calling the transition
        """
        logger = logging.getLogger('xworkflows.transitions')
        try:
            instance_repr = u(repr(instance), 'ignore')
        except (UnicodeEncodeError, UnicodeDecodeError):
            instance_repr = u("<bad repr>")
        logger.info(u("%s performed transition %s.%s (%s -> %s)"), instance_repr,
            self.__class__.__name__, transition.name, from_state.name,
            transition.target.name)


# Workaround for metaclasses on python2/3.
# Equivalent to:
# Python2
#
# class Workflow(BaseWorkflow):
#     __metaclass__ = WorkflowMeta
#
# Python3
#
# class Workflow(metaclass=WorkflowMeta):
#     pass

Workflow = WorkflowMeta('Workflow', (BaseWorkflow,), {})


class StateWrapper(object):
    """Slightly enhanced wrapper around a base State object.

    Knows about the workflow.
    """
    def __init__(self, state, workflow):
        self.state = state
        self.workflow = workflow
        for st in workflow.states:
            setattr(self, 'is_%s' % st.name, st.name == self.state.name)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.state == other.state
        elif isinstance(other, State):
            return self.state == other
        elif is_string(other):
            return self.state.name == other
        else:
            return NotImplemented

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return self.state.name

    def __repr__(self):
        return '<%s: %r>' % (self.__class__.__name__, self.state)

    def __getattr__(self, attr):
        if attr == 'state':
            raise AttributeError(
                'Trying to access attribute %s of a non-initialized %r object!'
                % (attr, self.__class__))
        else:
            return getattr(self.state, attr)

    if not is_python3:
        def __unicode__(self):
            return u(str(self))

    def __hash__(self):
        # A StateWrapper should compare equal to its name.
        return hash(self.state.name)

    def transitions(self):
        """Retrieve a list of transitions available from this state."""
        return self.workflow.transitions.available_from(self.state)


class StateProperty(object):
    """Property-like attribute holding the state of a WorkflowEnabled object.

    The state is stored in the internal __dict__ of the instance.
    """

    def __init__(self, workflow, state_field_name):
        super(StateProperty, self).__init__()
        self.workflow = workflow
        self.field_name = state_field_name

    def __get__(self, instance, owner):
        """Retrieve the current state of the 'instance' object."""
        if instance is None:
            return self
        state = instance.__dict__.get(self.field_name,
                                      self.workflow.initial_state)
        return StateWrapper(state, self.workflow)

    def __set__(self, instance, value):
        """Set the current state of the 'instance' object."""
        try:
            state = self.workflow.states[value]
        except KeyError:
            raise ValueError("Value %s is not a valid state for workflow %s." %
                    (value, self.workflow))
        instance.__dict__[self.field_name] = state

    def __str__(self):
        return 'StateProperty(%s, %s)' % (self.workflow, self.field_name)


class StateField(object):
    """Indicates that a given class attribute is actually a workflow state."""
    def __init__(self, workflow):
        self.workflow = workflow


class WorkflowEnabledMeta(type):
    """Base metaclass for all Workflow Enabled objects.

    Defines:
    - one class attribute for each the attached workflows,
    - a '_workflows' attribute, a dict mapping each field_name to the related
        Workflow,
    - a '_xworkflows_implems' attribute, a dict mapping each field_name to a
        dict of related ImplementationProperty.
    - one class attribute for each transition for each attached workflow
    """

    @classmethod
    def _add_workflow(mcs, field_name, state_field, attrs):
        """Attach a workflow to the attribute list (create a StateProperty)."""
        attrs[field_name] = StateProperty(state_field.workflow, field_name)

    @classmethod
    def _find_workflows(mcs, attrs):
        """Finds all occurrences of a workflow in the attributes definitions.

        Returns:
            dict(str => StateField): maps an attribute name to a StateField
                describing the related Workflow.
        """
        workflows = {}
        for attribute, value in attrs.items():
            if isinstance(value, Workflow):
                workflows[attribute] = StateField(value)
        return workflows

    @classmethod
    def _add_transitions(mcs, field_name, workflow, attrs, implems=None):
        """Collect and enhance transition definitions to a workflow.

        Modifies the 'attrs' dict in-place.

        Args:
            field_name (str): name of the field transitions should update
            workflow (Workflow): workflow we're working on
            attrs (dict): dictionary of attributes to be updated.
            implems (ImplementationList): Implementation list from parent
                classes (optional)

        Returns:
            ImplementationList: The new implementation list for this field.
        """
        new_implems = ImplementationList(field_name, workflow)
        if implems:
            new_implems.load_parent_implems(implems)
        new_implems.transform(attrs)

        return new_implems

    @classmethod
    def _register_hooks(mcs, cls, implems):
        for implem_list in implems.values():
            implem_list.register_hooks(cls)

    def __new__(mcs, name, bases, attrs):
        # Map field_name => StateField
        workflows = {}
        # Map field_name => ImplementationList
        implems = {}

        # Collect workflows and implementations from parents
        for base in reversed(bases):
            if hasattr(base, '_workflows'):
                workflows.update(base._workflows)
                implems.update(base._xworkflows_implems)

        workflows.update(mcs._find_workflows(attrs))

        # Update attributes with workflow descriptions, and collect
        # implementation declarations.
        for field, state_field in workflows.items():
            mcs._add_workflow(field, state_field, attrs)

            implems[field] = mcs._add_transitions(
                field, state_field.workflow, attrs, implems.get(field))

        # Set specific attributes for children
        attrs['_workflows'] = workflows
        attrs['_xworkflows_implems'] = implems

        cls = super(WorkflowEnabledMeta, mcs).__new__(mcs, name, bases, attrs)
        mcs._register_hooks(cls, implems)
        return cls


class BaseWorkflowEnabled(object):
    """Base class for all objects using a workflow.

    Attributes:
        workflows (dict(str, StateField)): Maps the name of a 'state_field' to
            the related Workflow
    """


# Workaround for metaclasses on python2/3.
# Equivalent to:
# Python2
#
# class WorkflowEnabled(BaseWorkflowEnabled):
#     __metaclass__ = WorkflowEnabledMeta
#
# Python3
#
# class WorkflowEnabled(metaclass=WorkflowEnabledMeta):
#     pass

WorkflowEnabled = WorkflowEnabledMeta('WorkflowEnabled', (BaseWorkflowEnabled,), {})
