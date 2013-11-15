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

        if self.backend.exists(receiver, self.newsletter_list, user=self.user):
            subscriber = NewsletterSubscriber.objects.get(email=receiver)

            if not subscriber.is_unsubscribed:
                raise forms.ValidationError(_(u"You already subscribe to this newsletter."))

        return receiver

    def save(self, user=None):
        self.backend.register(self.cleaned_data['receiver'], self.newsletter_list, get_language(), user or self.user)


class UnsubscribeForm(forms.Form):
    email = forms.EmailField(max_length=250, required=True)
    from_all = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        self.newsletter_list = kwargs.pop('newsletter_list', None)

        backend_klass = get_backend()

        self.backend = backend_klass()

        super(UnsubscribeForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email']

        if not self.backend.subscribed(email, self.newsletter_list):
            raise forms.ValidationError(_(u"You are not subscribed to this newsletter."))

        return email

    def save(self):
        from_all = self.cleaned_data['from_all']

        if from_all:
            self.backend.unregister(self.cleaned_data['email'])
        else:
            self.backend.unregister(self.cleaned_data['email'], self.newsletter_list)