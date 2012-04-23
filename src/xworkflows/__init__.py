# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Raphaël Barrois

__version__ = '0.2.4'
__author__ = 'Raphaël Barrois <raphael.barrois@polytechnique.org>'

from . import base

AbortTransition = base.AbortTransition
ForbiddenTransition = base.ForbiddenTransition
InvalidTransitionError = base.InvalidTransitionError
WorkflowError = base.WorkflowError

Workflow = base.Workflow
WorkflowEnabled = base.WorkflowEnabled

transition = base.transition
