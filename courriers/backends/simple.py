# -*- coding: utf-8 -*-
from .base import BaseBackend

from django.template.loader import render_to_string
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.utils import translation

from ..models import NewsletterSubscriber
from ..settings import DEFAULT_FROM_EMAIL, PRE_PROCESSORS
from ..utils import load_class


class SimpleBackend(BaseBackend):
    model = NewsletterSubscriber

    def subscribe(self, email, newsletter_list, lang=None, user=None):
        return self.model.objects.create(email=email, user=user,
                                         newsletter_list=newsletter_list, lang=lang)

    def register(self, email, newsletter_list, lang=None, user=None):
        if not self.exists(email, newsletter_list, lang=lang):
            subscriber = self.subscribe(email, newsletter_list, lang, user)
        else:
            for subscriber in self.all(email=email, newsletter_list=newsletter_list, lang=lang):
                if subscriber.is_unsubscribed:
                    subscriber.subscribe()

    def unregister(self, email, newsletter_list=None, user=None, lang=None):
        qs = self.model.objects.filter(email__iexact=email)

        if lang:
            qs = qs.filter(lang=lang)

        if not newsletter_list:
            for subscriber in qs:
                subscriber.unsubscribe(commit=True)
        else:
            if self.exists(email, newsletter_list):
                for subscriber in qs.filter(newsletter_list=newsletter_list):
                    subscriber.unsubscribe(commit=True)

    def exists(self, email, newsletter_list=None, user=None, lang=None):
        return self.all(email, user=user, lang=lang, newsletter_list=newsletter_list).exists()

    def all(self, email, user=None, lang=None, newsletter_list=None):
        qs = self.model.objects.filter(email__iexact=email).select_related('newsletter_list')

        if user:
            qs = qs.filter(user=user)

        if lang:
            qs = qs.filter(lang=lang)

        if newsletter_list:
            qs = qs.filter(newsletter_list=newsletter_list)

        return qs

    def subscribed(self, email, newsletter_list=None, user=None, lang=None):
        return (self.all(email, user=user, lang=lang, newsletter_list=newsletter_list)
                .filter(is_unsubscribed=False)
                .exists())

    def send_mails(self, newsletter, fail_silently=False):
        qs = self.model.objects.filter(newsletter_list=newsletter.newsletter_list).subscribed()

        if newsletter.languages:
            subscribers = qs.has_langs(newsletter.languages).prefetch_related('user')
        else:
            subscribers = qs.prefetch_related('user')

        connection = mail.get_connection(fail_silently=fail_silently)

        emails = []

        old_language = translation.get_language()

        for subscriber in subscribers:
            translation.activate(subscriber.lang)

            email = EmailMultiAlternatives(newsletter.name,
                                           render_to_string('courriers/newsletter_raw_detail.txt', {
                                               'object': newsletter,
                                               'subscriber': subscriber
                                           }),
                                           DEFAULT_FROM_EMAIL,
                                           [subscriber.email, ],
                                           connection=connection)

            html = render_to_string('courriers/newsletter_raw_detail.html', {
                'object': newsletter,
                'items': newsletter.items.all().prefetch_related('newsletter'),
                'subscriber': subscriber
            })

            for pre_processor in PRE_PROCESSORS:
                html = load_class(pre_processor)(html)

            email.attach_alternative(html, 'text/html')

            emails.append(email)

        translation.activate(old_language)

        results = connection.send_messages(emails)

        newsletter.sent = True
        newsletter.save(update_fields=('sent', ))

        return results
