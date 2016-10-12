# -*- coding: utf-8 -*-
from . import base


class NewsletterLift(base.NewsletterList):
    class Meta(base.NewsletterList.Meta):
        abstract = False
