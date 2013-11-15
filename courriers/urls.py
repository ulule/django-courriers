from django.conf.urls import patterns, url

from .views import (NewsletterListView,
                    NewsletterDetailView,
                    NewsletterRawDetailView,
                    NewsletterListUnsubscribeView)


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

    url(r'^(?P<slug>(\w+))/unsubscribe/$',
        NewsletterListUnsubscribeView.as_view(),
        name="newsletterlist_unsubscribe"),
)
