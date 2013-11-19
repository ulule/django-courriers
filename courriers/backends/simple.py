# -*- coding: utf-8 -*-
from .base import BaseBackend

from django.template.loader import render_to_string
from django.core import mail
from django.core.mail import EmailMultiAlternatives

from ..models import NewsletterSubscriber
from ..settings import DEFAULT_FROM_EMAIL


class SimpleBackend(BaseBackend):
    model = NewsletterSubscriber

    def subscribe(self, email, newsletter_list, lang=None, user=None):
        return self.model.objects.create(email=email, user=user,
                                         newsletter_list=newsletter_list, lang=lang)

    def register(self, email, newsletter_list, lang=None, user=None):
        if not self.exists(email, newsletter_list):
            subscriber = self.subscribe(email, newsletter_list, lang, user)
        else:
            subscriber = self.model.objects.get(email=email, newsletter_list=newsletter_list)

            if subscriber.is_unsubscribed:
                subscriber.subscribe()

    def unregister(self, email, newsletter_list=None, user=None):
        if not newsletter_list:
            for subscriber in self.model.objects.filter(email=email):
                subscriber.unsubscribe(commit=True)
        else:
            if self.exists(email, newsletter_list):
                self.model.objects.get(email=email, newsletter_list=newsletter_list).unsubscribe()

    def exists(self, email, newsletter_list=None, user=None):
        qs = self.all(email, user=user)

        if newsletter_list:
            qs = qs.filter(newsletter_list=newsletter_list)

        return qs.exists()

    def all(self, email, user=None):
        qs = self.model.objects.filter(email=email).select_related('newsletter_list')

        if user:
            qs = qs.filter(user=user)

        return qs

    def subscribed(self, email, newsletter_list, user=None):
        return self.model.objects.filter(email=email,
                                         newsletter_list=newsletter_list,
                                         is_unsubscribed=False).exists()

    def send_mails(self, newsletter, fail_silently=False):
        qs = self.model.objects.filter(newsletter_list=newsletter.newsletter_list).subscribed()

        if newsletter.languages:
            subscribers = qs.has_langs(newsletter.languages).prefetch_related('user')
        else:
            subscribers = qs.prefetch_related('user')

        connection = mail.get_connection(fail_silently=fail_silently)

        emails = []
        for subscriber in subscribers:
            email = EmailMultiAlternatives(newsletter.name, render_to_string('courriers/newsletter_raw_detail.txt', {
                'object': newsletter,
                'subscriber': subscriber
            }), DEFAULT_FROM_EMAIL, [subscriber.email, ], connection=connection)

            email.attach_alternative(render_to_string('courriers/newsletter_raw_detail.html', {
                'object': newsletter,
                'subscriber': subscriber
            }), 'text/html')

            emails.append(email)

        results = connection.send_messages(emails)

        newsletter.sent = True
        newsletter.save(update_fields=['sent'])

        return results
