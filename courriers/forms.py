from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import get_language

from .backends import get_backend
from .models import NewsletterSubscriber


class SubscriptionForm(forms.Form):
    receiver = forms.EmailField(max_length=250, required=True)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)

        backend_klass = get_backend()

        self.backend = backend_klass()

        super(SubscriptionForm, self).__init__(*args, **kwargs)

    def clean_receiver(self):
        receiver = self.cleaned_data['receiver']

        if self.backend.exists(receiver, user=self.user):
            raise forms.ValidationError(_(u"You already subscribe to this newsletter."))

        return receiver

    def save(self, user=None):
        self.backend.register(self.cleaned_data['receiver'], get_language(), user or self.user)


class UnsubscriptionForm(forms.Form):
    receiver = forms.EmailField(max_length=250, required=True)

    def __init__(self, *args, **kwargs):
        backend_klass = get_backend()

        self.backend = backend_klass()

        super(UnsubscriptionForm, self).__init__(*args, **kwargs)

    def clean_receiver(self):
        receiver = self.cleaned_data['receiver']

        if self.backend.exists(receiver):
            obj = NewsletterSubscriber.objects.get(email=receiver)
            if obj.is_unsubscribed:
                raise forms.ValidationError(_(u"You are not subscribed to this newsletter."))
        else:
            raise forms.ValidationError(_(u"You are not subscribed to this newsletter."))

        return receiver

    def save(self):
        self.backend.unregister(self.cleaned_data['receiver'])
