from django import forms
from django.utils.translation import ugettext_lazy as _, get_language

from .backends import get_backend
from .models import NewsletterSubscriber
from .tasks import subscribe, unsubscribe


class SubscriptionForm(forms.Form):
    receiver = forms.EmailField(max_length=250, required=True, widget=forms.TextInput(attrs={
        'placeholder': _(u"Your email"),
        'size': '30'
    }))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.newsletter_list = kwargs.pop('newsletter_list', None)
        self.lang = kwargs.pop('lang', get_language())

        backend_klass = get_backend()

        self.backend = backend_klass()

        super(SubscriptionForm, self).__init__(*args, **kwargs)

    def clean_receiver(self):
        receiver = self.cleaned_data['receiver']

        if self.backend.exists(receiver, self.newsletter_list, user=self.user, lang=self.lang):
            qs = NewsletterSubscriber.objects.filter(email__iexact=receiver,
                                                     newsletter_list_id=self.newsletter_list.id)

            if self.lang:
                qs = qs.filter(lang=self.lang)

            if not qs.get().is_unsubscribed:
                raise forms.ValidationError(_(u"You already subscribe to this newsletter."))

        return receiver

    def save(self, user=None):
        subscribe.delay(email=self.cleaned_data['receiver'],
                        lang=self.lang,
                        newsletter_list_id=getattr(self.newsletter_list, 'pk', None),
                        user_id=getattr(user or self.user, 'pk', None))


class UnsubscribeForm(forms.Form):
    email = forms.EmailField(max_length=250, required=True, widget=forms.TextInput(attrs={
        'placeholder': _(u"Your email"),
        'size': '30'
    }))
    from_all = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        self.newsletter_list = kwargs.pop('newsletter_list', None)

        backend_klass = get_backend()

        self.backend = backend_klass()

        super(UnsubscribeForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email']

        if not self.backend.subscribed(email, newsletter_list=self.newsletter_list):
            raise forms.ValidationError(_(u"You are not subscribed to this newsletter."))

        return email

    def save(self, user=None):
        from_all = self.cleaned_data.get('from_all', False)

        if from_all or not self.newsletter_list:
            unsubscribe.apply_async(kwargs={'email': self.cleaned_data['email'],
                                            'user_id': getattr(user, 'pk', None)})
        else:
            unsubscribe.apply_async(kwargs={'email': self.cleaned_data['email'],
                                            'newsletter_list_id': self.newsletter_list.pk,
                                            'user_id': getattr(user, 'pk', None)})
