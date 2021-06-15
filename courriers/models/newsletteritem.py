# -*- coding: utf-8 -*-
from courriers import base_models as base


class NewsletterItem(base.NewsletterItem):
    class Meta(base.NewsletterItem.Meta):
        abstract = False
