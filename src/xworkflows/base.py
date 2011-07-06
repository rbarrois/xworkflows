# coding: utf-8
"""Base components of XWorkflows."""

import functools
import re


class WorkflowError(Exception):
    """Base class for errors from the xworkflows module."""


class InvalidTransitionError(WorkflowError):
    """Raised when trying to perform a transition not available from current state."""


def _setup_states(sdef):
    """Create a StateList object from a 'states' Workflow attribute."""
    sts = []
    for state in sdef:
        if isinstance(state, State):
            st = state
        elif isinstance(state, str):
            st = State(state)
        elif len(state) == 2:
            name, title = state
            st = State(name, title)
        else:
            raise ValueError("Elements of the 'state' attribute of a "
                             "workflow should be a State object, a "
                             "string or a pair of strings; got %s "
                             "instead." % state)
        sts.append(st)
    return StateList(sts)


def _setup_transitions(tdef, states):
    """Create a TransitionList object from a 'transitions' Workflow attribute.

    Args:
        tdef: list of transition definitions
        states (StateList): already parsed state definitions.

    Returns:
        TransitionList: the list of transitions defined in the 'tdef' argument.
    """
    trs = []
    for transition in tdef:
        if isinstance(transition, TransitionDef):
            tr = transition.transition(states)
        elif len(transition) == 3:
            (name, source, target) = transition
            # TODO: check that 'source' and 'target' are State list/object.
            if isinstance(target, State):
                tr = Transition(name, source, target)
            else:
                tr = TransitionDef(name, source, target).transition(states)
        else:
            raise ValueError("Elements of the 'transition' attribute "
                             "a workflow should be a TransitionDef "
                             "object, a string or a pair of strings; "
                             "got %s instead." % transition)
        trs.append(tr)
    return TransitionList(trs)


def _collect_implementations(attrs, field_name, transitions, add_noop=True):
    """Collect the TransitionImplementation instances from an 'attributes' dict.

    This will collect all transition implementations related to a given set of
    transitions.

    Args:
        attrs (dict(str, object)): Maps attribute names to their value,
            typically from a class definition
        field_name (str): The name of the field in which the state within the
            workflow will be stored.
        transitions (TransitionList): List of transitions for which
            implementations should be collected.
        add_noop (bool): Whether to add 'NoOpTransitionImplementation' for
            missing implementations.

    Returns:
        dict(str, TransitionImplementation): Maps an attribute name to the
            adequate transition implementation.
    """
    implementations = {}
    seen_transitions = set()

    # Collect all TransitionImplementation in attributes
    for name, value in attrs.iteritems():
        if isinstance(value, TransitionImplementation):
            if value.transition not in transitions:
                # Skip unknown transition implementations
                continue
            else:
                implementations[name] = value
                seen_transitions.add(value.transition.name)
        elif callable(value):
            if name in transitions:
                if name in implementations:
                    raise ValueError()  # TODO
                implementations[name] = TransitionImplementation(transitions[name], field_name, value)
                seen_transitions.add(name)

    # Browse not implemented transitions and make sure they can be implemented
    # without conflicting with other attributes; if required, add a 'noop'
    # implementation.
    for transition in transitions:
        if transition.name not in seen_transitions:
            if transition.name in attrs:
                raise ValueError(
                    "Error for transition %s: no implementation is defined, "
                    "and the related attribute is not callable: %s" %
                    (transition, attrs[transition.name]))
            elif add_noop:
                implementations[transition.name] = NoOpTransitionImplementation(transition, field_name)
                seen_transitions.add(transition.name)

    return implementations


class WorkflowMeta(type):
    """Base metaclass for all Workflows.

    Sets the 'states', 'transitions', 'initial_state', and 'implementations'
    attributes.
    """

    def __new__(mcs, name, bases, attrs):

        if 'states' in attrs and 'transitions' in attrs and 'initial_state' in attrs:

            # States
            states = _setup_states(attrs['states'])
            attrs['states'] = states

            # Transitions
            transitions = _setup_transitions(attrs['transitions'], states)
            attrs['transitions'] = transitions

            # Initial state
            initial_state = attrs['initial_state']
            attrs['initial_state'] = states[initial_state]

            # Transition implementations
            implementations = _collect_implementations(attrs, attrs.get('state_field', 'state'), transitions)
            attrs['implementations'] = implementations

        return type.__new__(mcs, name, bases, attrs)


class Workflow(object):
    """Base class for all workflows.

    Attributes:
        states (StateList): list of states of this Workflow
        transitions (TransitionList): list of Transitions of this Workflow
        implementations (dict(str, TransitionImplementation): mapping of
            transition name to implementation
        initial_state (State): initial state for the Workflow
        state_field (str): name of the instance attribute holding the state of
            instances.

    For each transition, a TransitionImplementation with the same name (unless
    another name has been specified through the use of the @transition
    decorator) is provided to perform the specified transition.
    """
    __metaclass__ = WorkflowMeta

    state_field = None

    def __init__(self, state_field=None):
        """Create an instance of the workflow.

        This only allows overriding the 'state_field' attribute.
        """
        if state_field:
            self.state_field = state_field


def _find_workflows(attrs):
    """Find workflow definition(s) in a WorkflowEnabled definition."""
    workflows = {}
    for k, v in attrs.iteritems():
        # both Workflow definition and Workflow instances are allowed
        if isinstance(v, Workflow):
            wf = v
        elif isinstance(v, type) and issubclass(v, Workflow):
            wf = v()
        else:
            continue
        if wf.state_field:
            state_field = wf.state_field
        else:
            state_field = k
        if state_field in workflows:
            raise ValueError(
                "Unable to define the state field for workflow %s to "
                "%s since that name is already used for the state field of "
                "workflow %s." % (wf, state_field, workflows[state_field]))
        workflows[state_field] = wf
    return workflows


class WorkflowEnabledMeta(type):
    """Base metaclass for all Workflow Enabled objects.

    Defines:
    - one class attribute for each 'state_field' of the attached workflows,
    - a '_workflows' attribute, a dict mapping each state_field to the related
        Workflow,
    - one class attribute for each transition for each attached workflow.
    """
    def __new__(mcs, name, bases, attrs):
        workflows = _find_workflows(attrs)
        for state_field, workflow in workflows.iteritems():
            if state_field in attrs:
                raise ValueError(
                    "Unable to define the state field for workflow %s to %s "
                    "since there is already an attribute with that name in the "
                    "class definition (%s=%s)" %
                    (workflow, state_field, state_field, attrs[state_field]))
            attrs[state_field] = StateProperty(workflow, state_field)

            implems = _collect_implementations(attrs, state_field,
                    workflow.transitions, add_noop=False)

            implementations = workflow.implementations.copy()
            implementations.update(implems)

            # Browse transition implementations, and attach them to the class
            # definition. Fail on conflicts.
            for trname, implem in implementations.iteritems():
                if trname in attrs:
                    otherimpl = attrs[trname]
                    if not isinstance(otherimpl, TransitionImplementation):
                        raise ValueError(
                            "Conflict for method %s: it should be used as a "
                            "transition implementation for transition %s, but "
                            "is already defined as %s." %
                            (implem, trname, otherimpl))
                    elif otherimpl.transition != implem.transition:
                        raise ValueError(
                            "Conflict for method %s: there is already a "
                            "transition implementation for another transition "
                            "(%s) by that name." %
                            (implem, otherimpl))
                    else:
                        implem = otherimpl
                attrs[trname] = implem

        attrs['_workflows'] = workflows
        return super(WorkflowEnabledMeta, mcs).__new__(mcs, name, bases, attrs)


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
            return None
        state = instance.__dict__.get(self.field_name,
                                      self.workflow.initial_state)
        return StateField(state, self.workflow)

    def __set__(self, instance, value):
        """Set the current state of the 'instance' object."""
        if not value in self.workflow.states:
            raise ValueError("Value %s is not a valid state for workflow %s." %
                    (value, self.workflow))
        instance.__dict__[self.field_name] = value

    def __str__(self):
        return 'StateProperty(%s, %s)' % (self.workflow, self.field_name)


class StateField(object):
    def __init__(self, state, workflow):
        self.state = state
        self.workflow = workflow

    def __eq__(self, other_state):
        if not isinstance(other_state, State):
            return NotImplemented
        return self.state == other_state

    def __str__(self):
        return str(self.state)

    def __repr__(self):
        return repr(self.state)

    def __getattr__(self, attr):
        if attr.startswith('is_'):
            return self.state.name == attr[3:]

    def transitions(self):
        return self.workflow.transitions.available_from(self.state)


class WorkflowEnabled(object):
    """Base class for all objects using a workflow.

    Attributes:
        _workflows (dict(str, Workflow)): Maps the name of a 'state_field' to
            the related Workflow
    """
    __metaclass__ = WorkflowEnabledMeta



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
    """

    def __init__(self, transition, field_name, implementation):
        self.transition = transition
        self.field_name = field_name
        self.implementation = implementation


    def __get__(self, instance, owner):
        if instance is None:
            return self

        if not isinstance(instance, WorkflowEnabled):
            raise ValueError(
                "Unable to apply transition %s to object %s, which is not "
                "attached to a Workflow." % (self.transition, instance))

        @functools.wraps(self.implementation)
        def actual_implementation(*args, **kwargs):
            current_state = getattr(instance, self.field_name)
            if current_state not in self.transition.source:
                raise InvalidTransitionError(
                    "Transition %s isn't available from state %s." %
                    (self.transition, current_state))

            try:
                res = self.implementation(instance, *args, **kwargs)
            except AbortTransition:
                return None

            setattr(instance, self.field_name, self.transition.target)
            return res

        return actual_implementation


def noop(instance, *args, **kwargs):
    """NoOp function, ignores all arguments."""
    pass


class NoOpTransitionImplementation(TransitionImplementation):
    """A dummy transition implementation which does not perform any action."""

    def __init__(self, transition_name, field_name):
        super(NoOpTransitionImplementation, self).__init__(transition_name, field_name, noop)


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
        return '%s(%r, %r)' % (self.__class__.__name__, self.name, self.title)


class StateList(object):
    """A list of states."""
    def __init__(self, states):
        self._states = dict((st.name, st) for st in states)

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

    def __bool__(self):
        return bool(self._states)

    def __iter__(self):
        return self._states.itervalues()

    def __contains__(self, state):
        return isinstance(state, State) and state.name in self._states and self._states[state.name] == state


class TransitionDef(object):
    """A transition definition.

    Attributes:
        name (str): the name of the transition
        source (str list): the name of the source states for the transition
        target (str): the name of the target state for the transition
    """

    def __init__(self, name, source, target):
        self.name = name
        if isinstance(source, str):
            source = [source]
        self.source = source
        self.target = target

    def transition(self, states):
        sources = [states[source] for source in self.source]
        target = states[self.target]
        return Transition(self.name, sources, target)

    def __repr__(self):
        return '%s(%r, %r, %r)' % (self.__class__.__name__,
                                   self.name, self.source, self.target)


class TransitionList(object):
    """Holder for the transitions of a given workflow."""

    def __init__(self, transitions):
        """Create a TransitionList.

        Args:
            transitions (list of TransitionDef): the transitions to include.
        """
        self._transitions = {}
        for trdef in transitions:
            self._transitions[trdef.name] = trdef

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

    def __bool__(self):
        return bool(self._transitions)

    def __iter__(self):
        return self._transitions.itervalues()

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
