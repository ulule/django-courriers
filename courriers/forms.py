from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import get_language

from .backends import get_backend
from .models import NewsletterSubscriber


class SubscriptionForm(forms.Form):
    receiver = forms.EmailField(max_length=250, required=True)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.newsletter_list = kwargs.pop('newsletter_list', None)

        backend_klass = get_backend()

        self.backend = backend_klass()

        super(SubscriptionForm, self).__init__(*args, **kwargs)

    def clean_receiver(self):
        receiver = self.cleaned_data['receiver']

        if self.backend.exists(receiver, user=self.user):
            subscriber = NewsletterSubscriber.objects.get(email=receiver)

            if not subscriber.is_unsubscribed:
                raise forms.ValidationError(_(u"You already subscribe to this newsletter."))

        return receiver

    def save(self, user=None):
        self.backend.register(self.cleaned_data['receiver'], self.newsletter_list, get_language(), user or self.user)


class NewsletterListUnsubscribeForm(forms.Form):
    from_all = forms.BooleanField()

    def __init__(self, *args, **kwargs):
        self.newsletter_list = kwargs.pop('newsletter_list')
        self.receiver = kwargs.pop('receiver', None)

        backend_klass = get_backend()

        self.backend = backend_klass()

        super(NewsletterListUnsubscribeForm, self).__init__(*args, **kwargs)

    def clean_receiver(self):
        receiver = self.cleaned_data['receiver']

        if not self.backend.subscribed(receiver):
            raise forms.ValidationError(_(u"You are not subscribed to this newsletter."))

        return receiver

    def save(self):
        from_all = self.cleaned_data['from_all']

        if from_all:
            self.backend.unregister(self.receiver)
        else:
            self.backend.unregister(self.receiver, self.newsletter_list)
