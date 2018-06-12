import django.dispatch

unsubscribed = django.dispatch.Signal(
    providing_args=["user", "newsletter_list", "email"]
)

subscribed = django.dispatch.Signal(providing_args=["user", "newsletter_list", "email"])
