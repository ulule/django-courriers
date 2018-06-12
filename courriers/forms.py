from django import forms
from django.utils.translation import ugettext_lazy as _

from .backends import get_backend
from .tasks import subscribe, unsubscribe


class SubscriptionForm(forms.Form):
    receiver = forms.EmailField(
        max_length=250,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": _(u"Your email"), "size": "30"}),
    )

    def __init__(self, *args, **kwargs):
        self.newsletter_list = kwargs.pop("newsletter_list", None)

        backend_klass = get_backend()

        self.backend = backend_klass()

        super(SubscriptionForm, self).__init__(*args, **kwargs)

    def save(self, user=None):
        subscribe.delay(
            self.cleaned_data.get("receiver"),
            self.newsletter_list.pk,
            user_id=user.pk if user else None,
        )


class UnsubscribeForm(forms.Form):
    email = forms.EmailField(
        max_length=250,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": _(u"Your email"), "size": "30"}),
    )
    from_all = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        self.newsletter_list = kwargs.pop("newsletter_list", None)

        backend_klass = get_backend()

        self.backend = backend_klass()

        super(UnsubscribeForm, self).__init__(*args, **kwargs)

    def save(self, user=None):
        from_all = self.cleaned_data.get("from_all", False)

        if from_all or not self.newsletter_list:
            unsubscribe.delay(
                self.cleaned_data.get("email"), user_id=getattr(user, "pk", None)
            )
        else:
            unsubscribe.delay(
                self.cleaned_data["email"],
                newsletter_list_id=self.newsletter_list.pk,
                user_id=getattr(user, "pk", None),
            )
