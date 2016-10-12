# -*- coding: utf-8 -*-
from . import base


class NewsletterSubscriber(base.NewsletterSubscriber):
    class Meta(base.NewsletterSubscriber.Meta):
        abstract = False
