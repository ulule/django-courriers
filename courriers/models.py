# -*- coding: utf-8 -*-
import os

from django.db import models
from django.db.models.query import QuerySet

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from django.template.defaultfilters import slugify, truncatechars
from django.utils.translation import ugettext_lazy as _

from datetime import datetime


def get_file_path(instance, filename):
    fname, ext = os.path.splitext(filename)
    filename = unicode('%s%s' % (slugify(truncatechars(fname, 50)), ext))

    return os.path.join('courriers', 'uploads', filename)



class NewsletterQuerySet(QuerySet):
    def status_online(self):
        return self.filter(status=Newsletter.STATUS_ONLINE, published_at__lt=datetime.now()) \
                    .order_by('published_at')

    def get_previous(self, current_date):
        qs = self.filter(published_at__lt=current_date).order_by('-published_at')[:1]
        if qs:
            return qs.get()
        return None

    def get_next(self, current_date):
        qs = self.filter(published_at__gt=current_date)[:1]
        if qs:
            return qs.get()
        return None



class NewsletterManager(models.Manager):
    def get_query_set(self):
        return NewsletterQuerySet(self.model)

    def status_online(self):
        return self.get_query_set().status_online()

    def get_previous(self, current_date):
        return self.status_online().get_previous(current_date)

    def get_next(self, current_date):
        return self.status_online().get_next(current_date)



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

    objects = NewsletterManager()

    def __unicode__(self):
        return self.name



class NewsletterItem(models.Model):
    newsletter = models.ForeignKey(Newsletter, related_name="items")
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to=get_file_path, blank=True, null=True)
    url = models.URLField(blank=True, null=True)



class NewsletterSubscriberQuerySet(QuerySet):
    def subscribed(self):
        return self.filter(is_unsubscribed=False)


class NewsletterSubscriberManager(models.Manager):
    def get_query_set(self):
        return NewsletterSubscriberQuerySet(self.model)

    def subscribed(self):
        return self.get_queryset().subscribed()


class NewsletterSubscriber(models.Model):
    subscribed_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, null=True)
    is_unsubscribed = models.BooleanField(default=False, db_index=True)
    email = models.EmailField(max_length=250, unique=True)

    objects = NewsletterSubscriberManager()

    def __unicode__(self):
        return self.user.username

    def unsubscribe(self, commit=True):
        self.is_unsubscribed = True

        if commit:
            self.save(updated_fields=('is_unsubscribed', ))