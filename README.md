## LinuxForHealth XWorkflows
LinuxForHealth XWorkflows is a fork of [XWorkflows](https://github.com/rbarrois/xworkflows), a library to add workflows, or state machines, to Python objects.
This LinuxForHealth fork supports Python version >= 3.8 and is utilized within the LinuxForHealth ecosystem to define and execute workflow based processing.

##Links
- Package on PyPI: https://pypi.python.org/pypi/lfh-xworkflows
- GitHub Issues: https://github.com/linuxforhealth/xworkflows

## Getting Started
#### Clone the project and navigate to the root directory
```shell
git clone https://github.com/LinuxForHealth/xworkflows
cd xworkflows
```

#### Create a virtual environment
```shell
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

#### Install XWorkflows with dev and test dependencies
```shell
pip install -e .[dev,test]
# note if using zsh shell the extra dependencies require quoting
# pip install -e ".[dev,test]"
```

#### run tests
```shell
pytest
```

## Tutorial
XWorkflows is used to define and consume class based workflows. Workflows are defined by extending the Workflow class and providing states and transitions.
Workflows are implemented by attaching a workflow definition to a WorkflowEnabled class.

```python
import xworkflows

class MyWorkflow(xworkflows.Workflow):
    # A list of state names
    states = (
        ('foo', "Foo"),
        ('bar', "Bar"),
        ('baz', "Baz"),
    )
    # A list of transition definitions; items are (name, source states, target).
    transitions = (
        ('foobar', 'foo', 'bar'),
        ('gobaz', ('foo', 'bar'), 'baz'),
        ('bazbar', 'baz', 'bar'),
    )
    initial_state = 'foo'


class MyObject(xworkflows.WorkflowEnabled):
    state = MyWorkflow()

    @xworkflows.transition()
    def foobar(self):
        return 42

    # It is possible to use another method for a given transition.
    @xworkflows.transition('gobaz')
    def blah(self):
        return 13
```

```python
>>> o = MyObject()
>>> o.state
<StateWrapper: <State: 'foo'>>
>>> o.state.is_foo
True
>>> o.state.name
'foo'
>>> o.state.title
'Foo'
>>> o.foobar()
42
>>> o.state
<StateWrapper: <State: 'bar'>>
>>> o.state.name
'bar'
>>> o.state.title
'Bar'
>>> o.blah()
13
>>> o.state
<StateWrapper: <State: 'baz'>>
>>> o.state.name
'baz'
>>> o.state.title
'Baz'
```

XWorkflows supports event based integration using custom functions or "hooks". Events are raised for:
- before_transition
- after_transition
- on_enter_state
- on_leave_state

```python
class MyObject(xworkflows.WorkflowEnabled):

    state = MyWorkflow()

    @xworkflows.before_transition('foobar')
    def my_hook(self, *args, **kwargs):
        # *args and **kwargs are those passed to MyObject.foobar(...)
        pass

    @xworkflows.on_enter_state('bar')
    def my_other_hook(self, result, *args, **kwargs):
        # Will be called just after any transition entering 'bar'
        # result is the value returned by that transition
        # *args, **kwargs are the arguments/keyword arguments passed to the
        # transition.
        pass
```
