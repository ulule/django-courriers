from django.conf.urls import patterns, url

from .views import (NewsletterListView,
                    NewsletterDetailView,
                    NewsletterRawDetailView,
                    NewsletterUnsubscribeView,
                    send_newsletter)


urlpatterns = patterns(
    '',
    url(r'^$',
        NewsletterListView.as_view(),
        name="newsletter_list"),

    url(r'^(?P<pk>(\d+))/$',
        NewsletterDetailView.as_view(),
        name="newsletter_detail"),

    url(r'^(?P<pk>(\d+))/raw/$',
        NewsletterRawDetailView.as_view(),
        name="newsletterraw_detail"),

    url(r'^unsubscribe/$',
        NewsletterUnsubscribeView.as_view(),
        name="newsletterraw_unsubscribe"),

    url(r'^send/(?P<newsletter_id>(\d+))/$',
        send_newsletter,
        name='send_newsletter'),
)
