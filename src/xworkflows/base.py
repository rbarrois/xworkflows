# coding: utf-8
"""Base components of XWorkflows."""

import functools
import inspect
import logging
import re


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

    def __init__(self, name, title=None):
        if not self.STATE_NAME_RE.match(name):
            raise ValueError('Invalid state name %s.' % name)
        self.name = name
        if not title:
            title = name
        self.title = title

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

    def __getitem__(self, name):
        return self._states[name]

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
        else:
            name, title = state_def
            state = State(name, title)
        if state in states:
            # Replacing an existing state
            states.remove(state)
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
            if isinstance(source, basestring) or isinstance(source, State):
                source = [source]
            source = [states[src] for src in source]
            target = states[target]
            tr = Transition(name, source, target)
        else:
            raise TypeError("Elements of the 'transition' attribute of a "
                "workflow should be three-tuples; got %r instead." % (transition,))

        at = None
        for i, prev_tr in enumerate(trs):
            if tr.name == prev_tr.name:
                at = i
        if at is not None:
            trs[at] = tr
        else:
            trs.append(tr)
    return TransitionList(trs)


class TransitionImplementation(object):
    """Holds an implementation of a transition.

    This class is a 'non-data descriptor', somewhat similar to a property.

    The 'implementation' callable is called with the modified object as its
    first argument; it may raise a AbortTransition exception to cancel the
    transition.

    Attributes:
        transition (Transition): the related transition
        field_name (str): the name of the field storing the state (which should
            be modified when the transition is called)
        implementation (callable): the actual function to call when performing
            the transition.
        before (callable): optional callable to call *before* performing the
            transition (but after state checks). If the return value evaluates
            to False, the transition will be silently aborted.
        after (callable): optional callable to call *after* performing the
            transition (once the state has changed).
    """
    def __init__(self, transition, field_name, workflow, implementation, check=None, before=None, after=None):
        self.transition = transition
        self.field_name = field_name
        self.workflow = workflow
        self.check = check
        self.before = before
        self.implementation = implementation
        self.after = after
        self.__doc__ = implementation.__doc__

    def __get__(self, instance, owner):
        if instance is None:
            return self

        if not isinstance(instance, BaseWorkflowEnabled):
            raise TypeError(
                "Unable to apply transition %s to object %s, which is not "
                "attached to a Workflow." % (self.transition, instance))

        @functools.wraps(self.implementation)
        def actual_implementation(*args, **kwargs):
            return self._run_implem(instance, *args, **kwargs)

        return actual_implementation

    def _check_state(self, instance):
        current_state = getattr(instance, self.field_name)
        if current_state not in self.transition.source:
            raise InvalidTransitionError(
                "Transition %s isn't available from state %s." %
                (self.transition, current_state))

    def _pre_transition(self, instance, *args, **kwargs):
        if self.check is not None:
            if not self.check(instance):
                raise ForbiddenTransition(
                    "Transition %s was forbidden by "
                    "custom pre-transition check." % self.transition.name)

        if self.before is not None:
            self.before(instance, *args, **kwargs)

    def _run_implem(self, instance, *args, **kwargs):
        """Run the transition, with all checks."""

        self._check_state(instance)
        # Call hooks.
        self._pre_transition(instance, *args, **kwargs)

        res = self._during_transition(instance, *args, **kwargs)

        from_state = getattr(instance, self.field_name)
        setattr(instance, self.field_name, self.transition.target)

        # Call hooks.
        self._log_transition(instance, from_state, *args, **kwargs)
        self._post_transition(instance, res, *args, **kwargs)
        return res

    def _during_transition(self, instance, *args, **kwargs):
        return self.implementation(instance, *args, **kwargs)

    def _log_transition(self, instance, from_state, *args, **kwargs):
        self.workflow.log_transition(self.transition, from_state, instance,
            *args, **kwargs)

    def _post_transition(self, instance, res, *args, **kwargs):
        """Performs post-transition actions."""
        if self.after is not None:
            self.after(instance, res, *args, **kwargs)

    def __repr__(self):
        return "<%s for %s on '%s': %s>" % (self.__class__.__name__, self.transition, self.field_name, self.implementation)


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
    if callable(trname):
        raise ValueError("The @transition decorator should be called as "
            "@transition(['transition_name'], **kwargs)")
    return TransitionWrapper(trname, field=field,
        check=check, before=before, after=after)


def noop(instance, *args, **kwargs):
    """NoOp function, ignores all arguments."""
    pass


class ImplementationList(object):
    """Stores all implementations.

    Attributes:
        state_field (str): the name of the field holding the state of objects.
        _implems (dict(str => TransitionImplementation)): maps an attribute name
            to the associated transition implementation.
        _transitions (TransitionList): list of expected transitions.
        _transitions_mapping (dict(str => str)): maps a transition name to the
            name of the attribute holding the related transition.
    """

    def __init__(self, state_field, workflow):
        self.state_field = state_field
        self._implems = {}
        self._transitions_mapping = {}
        self._workflow = workflow

    def _get_implem(self, transition_name):
        return self._implems[self._transitions_mapping[transition_name]]

    def collect(self, attrs):
        """Collect the implementations from a given attributes dict."""

        def add_implem(transition, attr_name, function, check=None, before=None, after=None):
            """Helper for adding a an implementation to the list."""
            implem = self._workflow.implementation_class(
                transition, self.state_field, self._workflow, function,
                check=check, before=before, after=after)
            self._implems[attr_name] = implem
            self._transitions_mapping[transition.name] = attr_name

        for name, value in attrs.iteritems():
            if isinstance(value, TransitionWrapper):
                if value.trname in self._workflow.transitions:
                    if value.field and value.field != self.state_field:
                        # Applying for another workflow
                        continue

                    transition = self._workflow.transitions[value.trname]

                    if value.trname in self._transitions_mapping:
                        # Some other function used @transition(value.trname)
                        other_implem = self._get_implem(value.trname)
                        raise ValueError(
                            "Error for attribute %s: it defines implementation "
                            "%s for transition %s, which is already implemented "
                            "as %s." % (name, value, transition,
                                self._get_implem(value.trname)))

                    add_implem(transition, name, value.func,
                        check=value.check, before=value.before, after=value.after)

    def _assert_may_override(self, implem, other, attrname):
        if isinstance(other, TransitionImplementation):
            # Another TransitionImplementation, but not the same transition/workflow
            if other.transition != implem.transition or other.field_name != implem.field_name:
                raise ValueError(
                    "Can't override transition implementation %s=%s with %s" %
                    (attrname, other, implem))
        elif isinstance(other, TransitionWrapper):
            # A TransitionWrapper, but not the same Transition
            if other.trname != implem.transition.name:
                raise ValueError(
                    "Can't override transition implementation %s=%s with %s" %
                    (attrname, other, implem))
        elif other != implem.implementation:
            # Anything else, and not what this TransitionImplementation wrap.
            raise ValueError(
                "Can't override attribute %s=%s with %s" %
                (attrname, other, implem))

    @classmethod
    def _add_implem(cls, attrs, attrname, implem):
        attrs[attrname] = implem

    def update_attrs(self, attrs):
        for transition in self._workflow.transitions:
            # Where to put the implementation
            attrname = transition.name

            if transition.name in self._transitions_mapping:
                # We had a custom implementation
                attrname = self._transitions_mapping[transition.name]
                implem = self._implems[attrname]
                if implem.transition != transition:
                    # Should never happen...
                    raise ValueError(
                        "Error for transition %s: implementation has been "
                        "overridden by %s." % (transition, implem))
            elif attrname in attrs:
                # No custom implementation, but name conflict.
                raise ValueError(
                    "Error for transition %s: no implementation is defined, "
                    "and the related attribute lacks a @transition "
                    "decorator: %s" % (transition, attrs[attrname]))

            else:
                # No custom implementation, no name conflict.
                # Create a 'noop' transition
                implem = self._workflow.implementation_class(
                    transition, self.state_field, self._workflow, noop)

            if attrname in attrs:
                self._assert_may_override(implem, attrs[attrname], attrname)

            self._add_implem(attrs, attrname, implem)
        return attrs

    def __getitem__(self, trname):
        attrname = self._transitions_mapping[trname]
        return self._implems[attrname]

    def __contains__(self, trname):
        if not trname in self._transitions_mapping:
            return False
        return self._transitions_mapping[trname] in self._implems

    def __repr__(self):
        return '<%s: %r>' % (self.__class__.__name__, self._implems.values())


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


class Workflow(object):
    """Base class for all workflows.

    Attributes:
        states (StateList): list of states of this Workflow
        transitions (TransitionList): list of Transitions of this Workflow
        initial_state (State): initial state for the Workflow
        implementation_class (TransitionImplementation subclass): class to use
            for transition implementation wrapping.

    For each transition, a TransitionImplementation with the same name (unless
    another name has been specified through the use of the @transition
    decorator) is provided to perform the specified transition.
    """
    __metaclass__ = WorkflowMeta

    implementation_class = TransitionImplementation

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
        logger.info(u'%r performed transition %s.%s (%s -> %s)', instance,
            self.__class__.__name__, transition.name, from_state.name,
            transition.target.name)


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
        if isinstance(other, State):
            return self.state == other
        elif isinstance(other, basestring):
            return self.state.name == other
        else:
            return NotImplemented

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return str(self.state)

    def __repr__(self):
        return '<%s: %r>' % (self.__class__.__name__, self.state)

    def __getattr__(self, attr):
        if attr == 'state':
            raise AttributeError(
                'Trying to access attribute %s of a non-initialized %r object!'
                % (attr, self.__class__))
        else:
            return getattr(self.state, attr)

    def __unicode__(self):
        return unicode(self.state.title)

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
        if not value in self.workflow.states:
            raise ValueError("Value %s is not a valid state for workflow %s." %
                    (value, self.workflow))
        instance.__dict__[self.field_name] = value

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
        for k, v in attrs.items():
            if isinstance(v, Workflow):
                workflows[k] = StateField(v)
        return workflows

    def __new__(mcs, name, bases, attrs):
        workflows = mcs._find_workflows(attrs)
        for field_name, state_field in workflows.iteritems():
            mcs._add_workflow(field_name, state_field, attrs)

            implems = ImplementationList(field_name, state_field.workflow)
            implems.collect(attrs)
            implems.update_attrs(attrs)

        attrs['_workflows'] = dict((field_name, state_field.workflow)
            for field_name, state_field in workflows.items())
        return super(WorkflowEnabledMeta, mcs).__new__(mcs, name, bases, attrs)


class BaseWorkflowEnabled(object):
    """Base class for all objects using a workflow.

    Attributes:
        _workflows (dict(str, Workflow)): Maps the name of a 'state_field' to
            the related Workflow
    """


class WorkflowEnabled(BaseWorkflowEnabled):
    __metaclass__ = WorkflowEnabledMeta
