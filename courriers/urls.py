from django.conf.urls import patterns, url

from .views import (NewsletterListView,
                    NewsletterDetailView,
                    NewsletterRawDetailView,
                    NewsletterListUnsubscribeView,
                    NewsletterListUnsubscribeDoneView)


urlpatterns = patterns(
    '',
    url(r'^(?P<pk>(\d+))/detail(?:/(?P<action>(\w+)))?/$',
        NewsletterDetailView.as_view(),
        name="newsletter_detail"),

    url(r'^(?P<pk>(\d+))/raw/$',
        NewsletterRawDetailView.as_view(),
        name="newsletter_raw_detail"),

    url(r'^(?:(?P<slug>(\w+))/)?unsubscribe/$',
        NewsletterListUnsubscribeView.as_view(),
        name="newsletter_list_unsubscribe"),

    url(r'^unsubscribe/(?:(?P<slug>(\w+))/)?done/$',
        NewsletterListUnsubscribeDoneView.as_view(),
        name="newsletter_list_unsubscribe_done"),

    url(r'^(?P<slug>(\w+))/(?:(?P<lang>(\w+))/)?(?:(?P<page>(\d+))/)?$',
        NewsletterListView.as_view(),
        name="newsletter_list"),
)
