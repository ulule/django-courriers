# -*- coding: utf-8 -*-
from .base import BaseBackend

from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import translation
from django.contrib.auth import get_user_model

from ..settings import DEFAULT_FROM_EMAIL, PRE_PROCESSORS
from ..utils import load_class

User = get_user_model()


class SimpleBackend(BaseBackend):
    def subscribe(self, list_id, email, lang=None, user=None):
        pass

    def unsubscribe(self, list_id, email, lang=None, user=None):
        pass

    def register(self, email, newsletter_list, lang=None, user=None):
        if not user:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = User.objects.create(email=email, username=email)

        user.subscribe(newsletter_list, lang=lang)

    def unregister(self, email, newsletter_list=None, user=None, lang=None):
        if not user:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return

        user.unsubscribe(newsletter_list, lang=lang)

    def send_mails(self, newsletter, fail_silently=False, subscribers=None):
        connection = mail.get_connection(fail_silently=fail_silently)

        emails = []

        old_language = translation.get_language()

        for subscriber in subscribers:
            if (
                newsletter.newsletter_segment.lang
                and newsletter.newsletter_segment.lang != subscriber.lang
            ):
                continue

            translation.activate(subscriber.lang)

            email = EmailMultiAlternatives(
                newsletter.name,
                render_to_string(
                    "courriers/newsletter_raw_detail.txt",
                    {"object": newsletter, "subscriber": subscriber},
                ),
                DEFAULT_FROM_EMAIL,
                [subscriber.email],
                connection=connection,
            )

            html = render_to_string(
                "courriers/newsletter_raw_detail.html",
                {
                    "object": newsletter,
                    "items": newsletter.items.all().prefetch_related("newsletter"),
                    "subscriber": subscriber,
                },
            )

            for pre_processor in PRE_PROCESSORS:
                html = load_class(pre_processor)(html)

            email.attach_alternative(html, "text/html")

            emails.append(email)

        translation.activate(old_language)

        results = connection.send_messages(emails)

        newsletter.sent = True
        newsletter.save(update_fields=("sent",))

        return results
