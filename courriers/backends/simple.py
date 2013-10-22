from .base import BaseBackend

from django.template.loader import render_to_string
from django.core.mail import send_mass_mail

from courriers.models import NewsletterSubscriber


class Backend(BaseBackend):
    model = NewsletterSubscriber

    def register(self, email, user=None):
        if user:
            new_subscriber = self.model(email=email, user=user)
        else:
            new_subscriber = self.model(email=email)
        new_subscriber.save()

    def unregister(self, email, user=None):
        if self.exists(email):
            self.model.get(email=email).unsubscribe()

    def exists(self, email, user=None):
        return self.model.objects.filter(email=email).exists()

    def send_mails(self, newsletter):
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