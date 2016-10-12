# -*- coding: utf-8 -*-
from . import base


class NewsletterList(base.NewsletterList):
    class Meta(base.NewsletterList.Meta):
        abstract = False
