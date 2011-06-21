Examples
========

Example of a workflow definition::

    class MyWorkflow(Workflow):

        states = ['init', 'ready', 'active', 'done', 'cancelled']

        transitions = [
            TransitionDef('prepare', 'init', 'ready'),
            TransitionDef('activate', 'ready', 'active'),
            TransitionDef('complete', 'active', 'done'),
            TransitionDef('cancel', ('ready', 'active'), 'cancelled'),
        ]

        @transition
        def prepare(self, obj):
            pass

        @transition
        def activate(self, obj):
            pass

Attributing the workflow to an object::

    class MyObject(WorkflowEnabled):
        workflow = MyWorkflow  # Or MyWorkflow()

        @transition
        def prepare(self):
            pass
