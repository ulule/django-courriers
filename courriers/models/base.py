from __future__ import unicode_literals

import os

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.template.defaultfilters import slugify, truncatechars
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone as datetime
from django.urls import reverse
from django.utils.encoding import python_2_unicode_compatible
from django.db.models.query import QuerySet

from ..settings import ALLOWED_LANGUAGES


def get_file_path(instance, filename):
    fname, ext = os.path.splitext(filename)
    filename = "{}{}".format(slugify(truncatechars(fname, 50)), ext)

    return os.path.join("courriers", "uploads", filename)


@python_2_unicode_compatible
class NewsletterList(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    list_id = models.IntegerField(null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name or ""

    def get_absolute_url(self):
        return reverse("newsletter_list", kwargs={"slug": self.slug})


@python_2_unicode_compatible
class NewsletterSegment(models.Model):
    name = models.CharField(max_length=255)
    segment_id = models.IntegerField()
    newsletter_list = models.ForeignKey(
        NewsletterList, on_delete=models.PROTECT, related_name="lists"
    )
    lang = models.CharField(
        max_length=10, blank=True, null=True, choices=ALLOWED_LANGUAGES
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.name or ""


class NewsletterQuerySet(QuerySet):
    def status_online(self):
        return self.filter(
            status=Newsletter.STATUS_ONLINE, published_at__lt=datetime.now()
        ).order_by("published_at")

    def get_previous(self, current_date):
        return (
            self.status_online()
            .filter(published_at__lt=current_date)
            .order_by("-published_at")
            .first()
        )

    def get_next(self, current_date):
        return (
            self.status_online()
            .filter(published_at__gt=current_date)
            .order_by("-published_at")
            .first()
        )


class NewsletterManager(models.Manager):
    def get_queryset(self):
        return NewsletterQuerySet(self.model)

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

    STATUS_CHOICES = ((STATUS_ONLINE, _("Online")), (STATUS_DRAFT, _("Draft")))

    name = models.CharField(max_length=255)
    published_at = models.DateTimeField(null=True)
    status = models.PositiveIntegerField(
        choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True
    )
    headline = models.TextField(blank=True, null=True)
    conclusion = models.TextField(blank=True, null=True)
    cover = models.ImageField(upload_to=get_file_path, blank=True, null=True)
    newsletter_list = models.ForeignKey(
        NewsletterList, related_name="newsletters", on_delete=models.PROTECT
    )
    newsletter_segment = models.ForeignKey(
        NewsletterSegment, related_name="segments", on_delete=models.PROTECT
    )
    sent = models.BooleanField(default=False, db_index=True)

    objects = NewsletterManager()

    class Meta:
        abstract = True

    def __str__(self):
        return self.name or ""

    def get_previous(self):
        return self.__class__.objects.filter(
            newsletter_list=self.newsletter_list_id
        ).get_previous(self.published_at)

    def get_next(self):
        return self.__class__.objects.filter(
            newsletter_list=self.newsletter_list_id
        ).get_next(self.published_at)

    def is_online(self):
        return self.status == self.STATUS_ONLINE

    def get_absolute_url(self):
        return reverse("newsletter_detail", args=[self.pk])


@python_2_unicode_compatible
class NewsletterItem(models.Model):
    newsletter = models.ForeignKey(
        Newsletter, related_name="items", on_delete=models.CASCADE
    )
    content_type = models.ForeignKey(
        ContentType, on_delete=models.PROTECT, blank=True, null=True
    )
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey("content_type", "object_id")
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to=get_file_path, blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    position = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["position"]
        abstract = True

    def __str__(self):
        return self.name or ""
