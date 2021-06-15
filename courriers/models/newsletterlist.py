# -*- coding: utf-8 -*-
from courriers import base_models as base


class NewsletterList(base.NewsletterList):
    class Meta(base.NewsletterList.Meta):
        abstract = False
