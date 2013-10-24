from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import get_language

from .backends import backend


class SubscriptionForm(forms.Form):
    receiver = forms.EmailField(max_length=250, required=True)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.backend = backend()

        super(SubscriptionForm, self).__init__(*args, **kwargs)

    def clean_receiver(self):
        receiver = self.cleaned_data['receiver']

        if self.backend.exists(receiver, user=self.user):
            raise forms.ValidationError(_(u"You already subscribe to this newsletter."))

        return receiver

    def save(self, user=None):
        self.backend.subscribe(self.cleaned_data['receiver'], 
                              get_language(),
                              user or self.user)
