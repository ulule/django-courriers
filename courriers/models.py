# -*- coding: utf-8 -*-
import os

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import slugify, truncatechars
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone as datetime

from .compat import User, update_fields
from .core import QuerySet, Manager
from .settings import ALLOWED_LANGUAGES


def get_file_path(instance, filename):
    fname, ext = os.path.splitext(filename)
    filename = unicode('%s%s' % (slugify(truncatechars(fname, 50)), ext))

    return os.path.join('courriers', 'uploads', filename)


class NewsletterQuerySet(QuerySet):
    def status_online(self):
        return (self.filter(status=Newsletter.STATUS_ONLINE,
                            published_at__lt=datetime.now())
                .order_by('published_at'))

    def get_previous(self, current_date):
        return (self.status_online()
                .filter(published_at__lt=current_date)
                .order_by('-published_at')
                .first())

    def get_next(self, current_date):
        return (self.status_online()
                .filter(published_at__gt=current_date)
                .order_by('-published_at')
                .first())


class NewsletterManager(Manager):
    def get_query_set(self):
        return NewsletterQuerySet(self.model)

    def status_online(self):
        return self.get_query_set().status_online()

    def get_previous(self, current_date):
        return self.get_query_set().get_previous(current_date)

    def get_next(self, current_date):
        return self.get_query_set().get_next(current_date)


class Newsletter(models.Model):
    STATUS_ONLINE = 1
    STATUS_DRAFT = 2

    STATUS_CHOICES = (
        (STATUS_ONLINE, _('Online')),
        (STATUS_DRAFT, _('Draft')),
    )

    name = models.CharField(max_length=255)
    published_at = models.DateTimeField(null=True)
    status = models.PositiveIntegerField(max_length=1,
                                         choices=STATUS_CHOICES,
                                         default=STATUS_DRAFT,
                                         db_index=True)
    headline = models.CharField(max_length=255, blank=True, null=True)
    cover = models.ImageField(upload_to=get_file_path, blank=True, null=True)
    lang = models.CharField(max_length=10, blank=True, null=True, choices=ALLOWED_LANGUAGES)

    objects = NewsletterManager()

    def __unicode__(self):
        return self.name

    def get_previous(self):
        return self.__class__.objects.get_previous(self.published_at)

    def get_next(self):
        return self.__class__.objects.get_next(self.published_at)

    def is_online(self):
        return self.status == self.STATUS_ONLINE


class NewsletterItem(models.Model):
    newsletter = models.ForeignKey(Newsletter, related_name="items")
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to=get_file_path, blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    def __unicode__(self):
        return self.description


class NewsletterSubscriberQuerySet(QuerySet):
    def subscribed(self):
        return self.filter(is_unsubscribed=False)

    def has_lang(self, lang):
        return self.filter(lang=lang)


class NewsletterSubscriberManager(models.Manager):
    def get_query_set(self):
        return NewsletterSubscriberQuerySet(self.model)

    def subscribed(self):
        return self.get_query_set().subscribed()

    def has_lang(self, lang):
        return self.get_query_set().has_lang(lang)


class NewsletterSubscriber(models.Model):
    subscribed_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, null=True)
    is_unsubscribed = models.BooleanField(default=False, db_index=True)
    email = models.EmailField(max_length=250, unique=True)
    lang = models.CharField(max_length=10, blank=True, null=True, choices=ALLOWED_LANGUAGES)

    objects = NewsletterSubscriberManager()

    def __unicode__(self):
        return self.email

    def subscribe(self, commit=True):
        self.is_unsubscribed = False

        if commit:
            update_fields(self, fields=('is_unsubscribed', ))

    def unsubscribe(self, commit=True):
        self.is_unsubscribed = True

        if commit:
            update_fields(self, fields=('is_unsubscribed', ))
