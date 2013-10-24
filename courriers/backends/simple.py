# -*- coding: utf-8 -*-
from .base import BaseBackend

from django.template.loader import render_to_string
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

from courriers.models import NewsletterSubscriber
from courriers.settings import DEFAULT_FROM_EMAIL


class SimpleBackend(BaseBackend):
    model = NewsletterSubscriber

    def subscribe(self, email, lang=None, user=None):
        if user:
            new_subscriber = self.model(email=email, user=user, lang=lang)
        else:
            new_subscriber = self.model(email=email, lang=lang)
        new_subscriber.save()

    def register(self, email, lang=None, user=None):
        if not self.exists(email):
            self.subscribe(email, lang, user)

    def unregister(self, email, user=None):
        if self.exists(email):
            self.model.objects.get(email=email).unsubscribe()

    def exists(self, email, user=None):
        return self.model.objects.filter(email=email).exists()

    def send_mails(self, newsletter, fail_silently=False):

        qs = self.model.objects.subscribed()

        if newsletter.lang:
            subscribers = qs.has_lang(newsletter.lang).prefetch_related('user')
        else:
            subscribers = qs.prefetch_related('user')

        connection = mail.get_connection(fail_silently=fail_silently)

        emails = []
        for subscriber in subscribers:
            email = EmailMultiAlternatives(newsletter.name, render_to_string('courriers/newsletterraw_detail.txt', {
                'object': newsletter,
                'subscriber': subscriber
            }), DEFAULT_FROM_EMAIL, [subscriber.email, ], connection=connection)

            email.attach_alternative(render_to_string('courriers/newsletterraw_detail.html', {
                'object': newsletter,
                'subscriber': subscriber
            }), 'text/html')

            emails.append(email)

        results = connection.send_messages(emails)

        return results