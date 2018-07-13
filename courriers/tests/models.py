from django.db import models
from django.utils import timezone as datetime
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.auth.models import AbstractUser, UserManager
from django.dispatch import receiver

from courriers.compat import AUTH_USER_MODEL
from courriers.settings import ALLOWED_LANGUAGES
from courriers.models import NewsletterList
from courriers import signals


@receiver(signals.unsubscribed)
def handle_unsubscribed(user, newsletter_list=None, **kwargs):
    user.unsubscribe(newsletter_list.pk if newsletter_list else None)


@receiver(signals.subscribed)
def handle_subscribed(user, newsletter_list=None, **kwargs):
    user.subscribe(newsletter_list.pk if newsletter_list else None)


class User(AbstractUser):
    class Meta:
        abstract = False

    objects = UserManager()

    def subscribed(self, newsletter_list_id, lang=None):
        filters = {"user": self, "newsletter_list_id": newsletter_list_id}
        if lang:
            filters["lang"] = lang

        return NewsletterSubscriber.objects.filter(**filters).exists()

    def subscribe(self, newsletter_list_id, lang=None):
        if isinstance(newsletter_list_id, NewsletterList):
            newsletter_list_id = newsletter_list_id.pk

        if not self.subscribed(newsletter_list_id, lang=lang):
            NewsletterSubscriber.objects.create(
                subscribed_at=datetime.now(),
                user=self,
                email=self.email,
                lang=lang,
                newsletter_list_id=newsletter_list_id,
            )
        else:
            (
                NewsletterSubscriber.objects.filter(
                    user=self, newsletter_list_id=newsletter_list_id, lang=lang
                ).update(unsubscribed_at=None, is_unsubscribed=False)
            )

    def unsubscribe(self, newsletter_list_id=None, lang=None):
        if isinstance(newsletter_list_id, NewsletterList):
            newsletter_lists = [newsletter_list_id.pk]
        elif newsletter_list_id:
            newsletter_lists = NewsletterList.objects.filter(
                pk=newsletter_list_id
            ).values_list("pk", flat=True)
        else:
            newsletter_lists = NewsletterList.objects.all().values_list("pk", flat=True)

        qs = NewsletterSubscriber.objects.filter(
            user=self, email=self.email, newsletter_list_id__in=newsletter_lists
        )

        if lang:
            qs = qs.filter(lang=lang)

        qs.update(unsubscribed_at=datetime.now(), is_unsubscribed=True)


@python_2_unicode_compatible
class NewsletterSubscriber(models.Model):
    subscribed_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True
    )
    is_unsubscribed = models.BooleanField(default=False, db_index=True)
    unsubscribed_at = models.DateTimeField(blank=True, null=True)
    email = models.EmailField(max_length=250)
    lang = models.CharField(
        max_length=10, blank=True, null=True, choices=ALLOWED_LANGUAGES
    )
    newsletter_list = models.ForeignKey(
        NewsletterList, related_name="newsletter_subscribers", on_delete=models.CASCADE
    )

    def __str__(self):
        return "%s for %s" % (self.email, self.newsletter_list)

    @property
    def subscribed(self):
        return self.is_unsubscribed is False
