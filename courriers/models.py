# -*- coding: utf-8 -*-
import os
import django

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.contrib.contenttypes.fields import GenericForeignKey
from django.template.defaultfilters import slugify, truncatechars
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone as datetime
from django.core.urlresolvers import reverse
from django.utils.encoding import python_2_unicode_compatible
from django.db.models.query import QuerySet

from .compat import AUTH_USER_MODEL
from .settings import ALLOWED_LANGUAGES

from separatedvaluesfield.models import SeparatedValuesField


def get_file_path(instance, filename):
    fname, ext = os.path.splitext(filename)
    filename = unicode('%s%s' % (slugify(truncatechars(fname, 50)), ext))

    return os.path.join('courriers', 'uploads', filename)


class NewsletterListQuerySet(QuerySet):
    def has_lang(self, lang):
        return self.filter(Q(languages__contains=lang) | Q(languages__isnull=True) | Q(languages=''))


class NewsletterListManager(models.Manager):
    def get_queryset(self):
        return NewsletterListQuerySet(self.model)

    def has_lang(self, lang):
        return self.get_queryset().has_lang(lang)


@python_2_unicode_compatible
class NewsletterList(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    languages = SeparatedValuesField(max_length=50,
                                     blank=True,
                                     null=True,
                                     choices=ALLOWED_LANGUAGES)

    objects = NewsletterListManager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('newsletter_list', kwargs={
            'slug': self.slug
        })


class NewsletterQuerySet(QuerySet):
    def has_lang(self, lang):
        return self.filter(Q(languages__contains=lang) | Q(languages__isnull=True) | Q(languages=''))

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


class NewsletterManager(models.Manager):
    def get_queryset(self):
        return NewsletterQuerySet(self.model)

    def has_lang(self, lang):
        return self.get_queryset().has_lang(lang)

    def status_online(self):
        return self.get_queryset().status_online()

    def get_previous(self, current_date):
        return self.get_queryset().get_previous(current_date)

    def get_next(self, current_date):
        return self.get_queryset().get_next(current_date)


@python_2_unicode_compatible
class Newsletter(models.Model):
    STATUS_ONLINE = 1
    STATUS_DRAFT = 2

    STATUS_CHOICES = (
        (STATUS_ONLINE, _('Online')),
        (STATUS_DRAFT, _('Draft')),
    )

    name = models.CharField(max_length=255)
    published_at = models.DateTimeField(null=True)
    status = models.PositiveIntegerField(choices=STATUS_CHOICES,
                                         default=STATUS_DRAFT,
                                         db_index=True)
    headline = models.TextField(blank=True, null=True)
    conclusion = models.TextField(blank=True, null=True)
    cover = models.ImageField(upload_to=get_file_path, blank=True, null=True)
    languages = SeparatedValuesField(max_length=50, blank=True, null=True, choices=ALLOWED_LANGUAGES)
    newsletter_list = models.ForeignKey(NewsletterList, related_name='newsletters')
    sent = models.BooleanField(default=False, db_index=True)

    objects = NewsletterManager()

    def __str__(self):
        return self.name

    def get_previous(self):
        return (self.__class__.objects.filter(newsletter_list=self.newsletter_list_id)
                .get_previous(self.published_at))

    def get_next(self):
        return (self.__class__.objects.filter(newsletter_list=self.newsletter_list_id)
                .get_next(self.published_at))

    def is_online(self):
        return self.status == self.STATUS_ONLINE

    def get_absolute_url(self):
        return reverse('newsletter_detail', args=[self.pk, ])


@python_2_unicode_compatible
class NewsletterItem(models.Model):
    newsletter = models.ForeignKey(Newsletter, related_name="items")
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to=get_file_path, blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    position = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return self.name


class NewsletterSubscriberQuerySet(QuerySet):
    def subscribed(self):
        return self.filter(is_unsubscribed=False)

    def has_lang(self, lang):
        return self.filter(lang=lang)

    def has_langs(self, langs):
        filter_q = None

        for lang in langs:
            if filter_q is None:
                filter_q = models.Q(lang=lang)
            else:
                filter_q |= models.Q(lang=lang)

        return self.filter(filter_q)


class NewsletterSubscriberManager(models.Manager):
    def get_queryset(self):
        return NewsletterSubscriberQuerySet(self.model)

    def subscribed(self):
        return self.get_queryset().subscribed()

    def has_lang(self, lang):
        return self.get_queryset().has_lang(lang)

    def has_langs(self, langs):
        return self.get_queryset().has_langs(langs)


@python_2_unicode_compatible
class NewsletterSubscriber(models.Model):
    subscribed_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(AUTH_USER_MODEL, blank=True, null=True)
    is_unsubscribed = models.BooleanField(default=False, db_index=True)
    unsubscribed_at = models.DateTimeField(blank=True, null=True)
    email = models.EmailField(max_length=250)
    lang = models.CharField(max_length=10, blank=True, null=True, choices=ALLOWED_LANGUAGES)
    newsletter_list = models.ForeignKey(NewsletterList, related_name='newsletter_subscribers')

    objects = NewsletterSubscriberManager()

    def __str__(self):
        return '%s for %s' % (self.email, self.newsletter_list)

    @property
    def subscribed(self):
        return self.is_unsubscribed is False

    def subscribe(self, commit=True):
        self.is_unsubscribed = False

        if commit:
            self.save(update_fields=('is_unsubscribed', ))

    def unsubscribe(self, commit=True):
        self.is_unsubscribed = True
        self.unsubscribed_at = datetime.now()

        if commit:
            self.save(update_fields=('is_unsubscribed', 'unsubscribed_at', ))
