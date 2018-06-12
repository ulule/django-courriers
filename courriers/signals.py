import django.dispatch

unsubscribed = django.dispatch.Signal(providing_args=["user", "newsletterlist", "email"])

subscribed = django.dispatch.Signal(providing_args=["user", "newsletterlist", "email"])
