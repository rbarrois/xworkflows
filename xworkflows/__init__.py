# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois
# This code is distributed under the two-clause BSD License.

from . import base

__version__ = '1.0.4'
__author__ = 'Raphaël Barrois <raphael.barrois+xworkflows@polytechnique.org>'

# Errors
AbortTransition = base.AbortTransition
ForbiddenTransition = base.ForbiddenTransition
InvalidTransitionError = base.InvalidTransitionError
WorkflowError = base.WorkflowError

# Defining and applying workflows
Workflow = base.Workflow
WorkflowEnabled = base.WorkflowEnabled

# Decorators
transition = base.transition

# Hooks
before_transition = base.before_transition
after_transition = base.after_transition
transition_check = base.transition_check
on_enter_state = base.on_enter_state
on_leave_state = base.on_leave_state
