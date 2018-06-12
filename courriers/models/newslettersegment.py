# -*- coding: utf-8 -*-
from . import base


class NewsletterSegment(base.NewsletterSegment):
    class Meta(base.NewsletterSegment.Meta):
        abstract = False
