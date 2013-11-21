from django.conf.urls import patterns, url

from .views import (NewsletterListDetailView,
                    NewsletterDetailView,
                    NewsletterRawDetailView,
                    NewsletterListUnsubscribeView,
                    NewslettersUnsubscribeView,
                    UnsubscribeThanksView)


urlpatterns = patterns(
    '',
    url(r'^(?P<slug>(\w+))/$',
        NewsletterListDetailView.as_view(),
        name="newsletter_list"),

    url(r'^(?P<pk>(\d+))/detail/$',
        NewsletterDetailView.as_view(),
        name="newsletter_detail"),

    url(r'^(?P<pk>(\d+))/raw/$',
        NewsletterRawDetailView.as_view(),
        name="newsletter_raw_detail"),

    url(r'^(?P<slug>(\w+))/unsubscribe/$',
        NewsletterListUnsubscribeView.as_view(),
        name="newsletter_list_unsubscribe"),

    url(r'^unsubscribe/all/$',
        NewslettersUnsubscribeView.as_view(),
        name="newsletters_unsubscribe"),

    url(r'^unsubscribe/thanks/$',
        UnsubscribeThanksView.as_view(),
        name="unsubscribe_thanks"),
)
