Integration with Django
=======================

XWorkflows can be easily used for Django models.
For that purpose, have your model inherit from :class:`django.xworkflow.WorkflowEnabledModel`::

    class MyModel(WorkflowEnabledModel, models.Model):

        class Workflow:
            states = ['a', 'b', 'c']

            transition = [
                ('a2b', 'a', 'b'),
                ('2c', ('a', 'b'), 'c'),
            ]

            initial_state = 'a'


With this definition, the :class:`MyModel` model has a new field, :attr:`state`, which is
a :class:`django.db.models.CharField` whose :attr:`choices` and :attr:`default` are configured
from the related Workflow.

Transitions
-----------

All transitions are logged in the database, using the :class:`django.xworkflow.TransitionLog` model. This can be avoided by passing the extra argument ``log=False`` when calling
a transition method.

The code of each transition method is wrapped in a transaction, and committed only on success; this includes saving the object with its new state.
This behaviour can be avoided:

* By passing the extra argument ``save=False`` when calling the transition method
* By passing the extra argument ``save=False`` to the :func:`transition` decorator for this function

All transition method accept an extra keyword argument, ``user``, which should be an instance of :class:`django.contrib.auth.User`, used to attach the log message to the user.
