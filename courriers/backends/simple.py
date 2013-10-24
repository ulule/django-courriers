# -*- coding: utf-8 -*-
from .base import BaseBackend

from django.template.loader import render_to_string
from django.core.mail import send_mass_mail

from courriers.models import NewsletterSubscriber


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

    def send_mails(self, newsletter):

        if newsletter.lang:
            subscribers = self.model.objects.subscribed().has_lang(newsletter.lang).prefetch_related('user')
        else:
            subscribers = self.model.objects.subscribed().prefetch_related('user')

        emails = [(
            newsletter.name,
            render_to_string('courriers/newsletterraw_detail.html', {
                'object': newsletter,
                'subscriber': subscriber
            }),
            None,
            [subscriber.email],
        ) for subscriber in subscribers]

        send_mass_mail(emails, fail_silently=False)