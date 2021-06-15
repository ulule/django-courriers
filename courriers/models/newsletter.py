# -*- coding: utf-8 -*-
from courriers import base_models as base


class Newsletter(base.Newsletter):
    class Meta(base.Newsletter.Meta):
        abstract = False
