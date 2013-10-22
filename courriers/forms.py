from django import forms
from django.utils.translation import ugettext_lazy as _

from courriers.backends import backend


class SubscriptionForm(forms.Form):
    receiver = forms.EmailField(max_length=250, required=True)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.backend = backend()
        super(SubscriptionForm, self).__init__(*args, **kwargs)

    def clean_receiver(self):
        receiver = self.cleaned_data['receiver']
        print "clean_receiver"
        print self.backend.exists(receiver, user=self.user)

        if self.backend.exists(receiver, user=self.user):
            print "exists"
            raise forms.ValidationError(_(u"You already subscribe to this newsletter."))

        return receiver

    def save(self, user=None):
        self.backend.register(self.cleaned_data['receiver'], user)