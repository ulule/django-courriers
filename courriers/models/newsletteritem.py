# -*- coding: utf-8 -*-
from . import base


class NewsletterItem(base.NewsletterItem):
    class Meta(base.NewsletterItem.Meta):
        abstract = False
