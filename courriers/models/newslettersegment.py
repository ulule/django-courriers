# -*- coding: utf-8 -*-
from courriers import base_models as base


class NewsletterSegment(base.NewsletterSegment):
    class Meta(base.NewsletterSegment.Meta):
        abstract = False
