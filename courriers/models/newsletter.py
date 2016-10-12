# -*- coding: utf-8 -*-
from . import base


class Newsletter(base.Newsletter):
    class Meta(base.Newsletter.Meta):
        abstract = False
