# coding: utf-8
"""Base components of XWorkflows."""

import functools
import inspect
import re


class WorkflowError(Exception):
    """Base class for errors from the xworkflows module."""


class InvalidTransitionError(WorkflowError):
    """Raised when trying to perform a transition not available from current state."""


class AbortTransition(WorkflowError):
    """Raised to prevent a transition from proceeding."""


class AbortTransitionSilently(WorkflowError):
    """Raised to (silently) prevent a transition from proceeding."""


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
            raise TypeError("Elements of the 'state' attribute of a "
                "workflow should be a State object, a string or a pair of "
                "strings; got %s instead." % (state,))
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
            raise TypeError("Elements of the 'transition' attribute of a "
                "workflow should be a TransitionDef object, a string or a "
                "pair of strings; got %s instead." % (transition,))
        trs.append(tr)
    return TransitionList(trs)


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
            implementations = ImplementationList(attrs.get('state_field', 'state'),
                                                 transitions)
            implementations.collect(attrs)
            attrs['implementations'] = implementations

        else:
            pass
        # TODO: allow subclassing.

        return super(WorkflowMeta, mcs).__new__(mcs, name, bases, attrs)


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
    renamed_state_fields = set()

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
            renamed_state_fields.add(state_field)
        else:
            state_field = k
        if state_field in workflows:
            raise ValueError(
                "Unable to define the state field for workflow %s to "
                "%s since that name is already used for the state field of "
                "workflow %s." % (wf, state_field, workflows[state_field]))
        workflows[state_field] = wf
    return (workflows, renamed_state_fields)


class WorkflowEnabledMeta(type):
    """Base metaclass for all Workflow Enabled objects.

    Defines:
    - one class attribute for each 'state_field' of the attached workflows,
    - a '_workflows' attribute, a dict mapping each state_field to the related
        Workflow,
    - one class attribute for each transition for each attached workflow; if an
        implementation was defined in the workflow, it keeps its name in the
        WorkflowEnabled object.
    """

    @classmethod
    def _add_workflow(mcs, workflow, state_field, attrs):
        """Attach a workflow to the attribute list (create a StateProperty)."""
        attrs[state_field] = StateProperty(workflow, state_field)

    @classmethod
    def _copy_implems(mcs, workflow, state_field):
        """Copy transition implementations from the workflow."""
        return ImplementationList.copy_from(workflow.implementations,
                                            state_field=state_field)

    def __new__(mcs, name, bases, attrs):
        workflows, renamed_state_fields = _find_workflows(attrs)
        for state_field, workflow in workflows.iteritems():
            if state_field in attrs and state_field in renamed_state_fields:
                raise ValueError(
                    "Unable to define the state field for workflow %s to %s "
                    "since there is already an attribute with that name in the "
                    "class definition (%s=%s)" %
                    (workflow, state_field, state_field, attrs[state_field]))
            mcs._add_workflow(workflow, state_field, attrs)

            implems = mcs._copy_implems(workflow, state_field)
            implems.augment(attrs)

            implems.update_attrs(attrs)

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
            return self
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

    def __eq__(self, other):
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
        if attr.startswith('is_'):
            return self.state.name == attr[3:]
        elif attr == 'state':
            raise AttributeError(
                'Trying to access attribute %s of a non-initialized %r object!'
                % (attr, self.__class__))
        else:
            return getattr(self.state, attr)

    def __unicode__(self):
        return unicode(self.state.title)

    def __hash__(self):
        # A StateField should compare equal to its name.
        return hash(self.state.name)

    def transitions(self):
        return self.workflow.transitions.available_from(self.state)


class BaseWorkflowEnabled(object):
    """Base class for all objects using a workflow.

    Attributes:
        _workflows (dict(str, Workflow)): Maps the name of a 'state_field' to
            the related Workflow
    """


class WorkflowEnabled(BaseWorkflowEnabled):
    __metaclass__ = WorkflowEnabledMeta



class TransitionImplementation(object):
    """Holds an implementation of a transition.

    This class is a 'non-data descriptor', somewhat similar to a property.

    The 'implementation' callable is called with the modified object as its
    first argument; it may raise a AbortTransition exception to cancel the
    transition.

    Attributes:
        extra_kwargs_kept (str list): list of extra keyword args captured by the
            TransitionImplementation, but also expected by the actual
            implementation; they won't be removed from the passed arguments.
        transition (Transition): the related transition
        field_name (str): the name of the field storing the state (which should
            be modified when the transition is called)
        implementation (callable): the actual function to call when performing
            the transition.
    """
    extra_kwargs = {}

    def __init__(self, transition, field_name, implementation):
        self.transition = transition
        self.field_name = field_name
        self.implementation = implementation
        argspec = inspect.getargspec(implementation)
        self.extra_kwargs_kept = [arg for arg in self.extra_kwargs if arg in argspec.args]
        self.__doc__ = implementation.__doc__

    def copy(self, field_name=None):
        if field_name is None:
            field_name = self.field_name
        return TransitionImplementation(self.transition, field_name, self.implementation)

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

    def _run_implem(self, instance, *args, **kwargs):
        cls_kwargs = {}
        for kwarg, default in self.extra_kwargs.iteritems():
            if kwarg in self.extra_kwargs_kept:
                val = kwargs.get(kwarg, default)
            else:
                val = kwargs.pop(kwarg, default)
            cls_kwargs[kwarg] = val

        self._check_state(instance)
        try:
            res = self._call_implem(instance, cls_kwargs, *args, **kwargs)
        except AbortTransitionSilently:
            return None
        self._post_transition(instance, res, cls_kwargs, *args, **kwargs)
        return res

    def _call_implem(self, instance, cls_kwargs, *args, **kwargs):
        return self.implementation(instance, *args, **kwargs)

    def _post_transition(self, instance, res, cls_kwargs, *args, **kwargs):
        setattr(instance, self.field_name, self.transition.target)

    def __repr__(self):
        return "<%s for %s on '%s': %s>" % (self.__class__.__name__, self.transition, self.field_name, self.implementation)


def noop(instance, *args, **kwargs):
    """NoOp function, ignores all arguments."""
    pass


class NoOpTransitionImplementation(TransitionImplementation):
    """A dummy transition implementation which does not perform any action."""

    def __init__(self, transition_name, field_name):
        super(NoOpTransitionImplementation, self).__init__(transition_name, field_name, noop)


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

    def __init__(self, state_field, transitions):
        self.state_field = state_field
        self._implems = {}
        self._transitions_mapping = {}
        self._transitions = transitions

    def collect(self, attrs):
        """Collect the implementations from a given attributes dict."""
        self.augment(attrs)

    @classmethod
    def copy_from(cls, implemlist, state_field):
        copy = cls(state_field, implemlist._transitions)
        copy._transitions_mapping = implemlist._transitions_mapping.copy()
        for attr, implem in implemlist._implems.iteritems():
            copy._implems[attr] = implem.copy(field_name=state_field)

        return copy

    def augment(self, attrs):
        """Augment the list of implementations from a given attributes dict."""
        # Store the transition name => attribute name mapping for
        # implementations discovered in the attrs dict
        _local_mappings = {}

        # Store the transition name => callable for callable which may be used
        # as transition implementations
        _remaining_candidates = {}

        # First, try to find all TransitionImplementation and TransitionWrapper.
        for name, value in attrs.iteritems():
            if isinstance(value, TransitionImplementation):
                if value.transition in self._transitions:
                    if value.field_name != self.state_field:
                        # State_field was overriden at some point
                        value = value.copy(field_name=self.state_field)
                    self._implems[name] = value
                    _local_mappings[value.transition.name] = name
            elif isinstance(value, TransitionWrapper):
                if value.trname in self._transitions:
                    transition = self._transitions[value.trname]
                    if value.trname in _local_mappings:
                        raise ValueError(
                            "Error for attribute %s: it defines implementation "
                            "%s for transition %s, which is already implemented "
                            "as %s." % (name, value, transition,
                                self._implems[_local_mappings[value.trname]]))
                    implem = value.get_implem(transition, self.state_field)
                    self._implems[name] = implem
                    _local_mappings[transition.name] = name
            elif callable(value):
                if name in self._transitions:
                    _remaining_candidates[name] = value

        # Then, browse the remaining transitions and add callable if needed.
        _implemented = self._transitions_mapping.copy()
        _implemented.update(_local_mappings)

        for transition in self._transitions:
            trname = transition.name
            if trname in _remaining_candidates:
                if trname not in _implemented or _implemented[trname] == trname:
                    value = _remaining_candidates[transition.name]
                    implem = TransitionImplementation(transition, self.state_field,
                                                      value)
                    _local_mappings[transition.name] = transition.name
                    self._implems[transition.name] = implem

        self._transitions_mapping.update(_local_mappings)

    def _assert_may_override(self, implem, other, attrname):
        if isinstance(other, TransitionImplementation):
            if other.transition != implem.transition or other.field_name != implem.field_name:
                raise ValueError(
                    "Can't override transition implementation %s=%s with %s" %
                    (attrname, other, implem))
        elif isinstance(other, TransitionWrapper):
            if other.trname != implem.transition.name:
                raise ValueError(
                    "Can't override transition implementation %s=%s with %s" %
                    (attrname, other, implem))
        elif other != implem.implementation:
            raise ValueError(
                "Can't override attribute %s=%s with %s" %
                (attrname, other, implem))

    @classmethod
    def _add_implem(cls, attrs, attrname, implem):
        attrs[attrname] = implem

    def update_attrs(self, attrs):
        for transition in self._transitions:
            trname = transition.name
            if transition.name in self._transitions_mapping:
                attrname = self._transitions_mapping[transition.name]
                implem = self._implems[attrname]
                if implem.transition != transition:
                    raise ValueError(
                        "Error for transition %s: implementation has been "
                        "overridden by %s." % (transition, implem))
            else:
                attrname = transition.name
                if attrname in attrs:
                    raise ValueError(
                        "Error for transition %s: no implementation is defined, "
                        "and the related attribute is not callable: %s" %
                        (transition, attrs[attrname]))

                implem = NoOpTransitionImplementation(transition, self.state_field)
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


def transition(trname):
    """Decorator to declare a function as a transition implementation.

    This should be used only when that function should be used for a transition
    with a different name.
    """

    return TransitionWrapper(trname)


class TransitionWrapper(object):

    def __init__(self, trname):
        self.trname = trname
        self.func = None

    def __call__(self, func):
        self.func = func
        return self

    def get_implem(self, transition, field_name):
        if transition.name != self.trname:
            raise ValueError(
                "Can't use a TransitionWrapper %s for transition %s." %
                (self.trname, transition))
        return TransitionImplementation(transition, field_name, self.func)

    def __repr__(self):
        return "<%s for %r: %s>" % (self.__class__.__name__, self.trname, self.func)


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
        if title is None:
            title = name
        self.title = title

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.name, self.title)


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
