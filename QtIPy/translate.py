#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .qt import QCoreApplication


def tr(s, *args, **kwargs):
    try:
        return QCoreApplication.translate('@default', s, *args, **kwargs)
    except:
        return s
