from django.conf.urls import url

from .views import (NewsletterListView,
                    NewsletterDetailView,
                    NewsletterListSubscribeView,
                    NewsletterRawDetailView,
                    NewsletterListUnsubscribeView,
                    NewsletterListSubscribeDoneView,
                    NewsletterListUnsubscribeDoneView)


urlpatterns = [
    url(r'^(?P<pk>(\d+))/detail/$',
        NewsletterDetailView.as_view(),
        name="newsletter_detail"),

    url(r'^(?P<slug>(\w+))/subscribe/$',
        NewsletterListSubscribeView.as_view(),
        name="newsletter_list_subscribe"),

    url(r'^(?P<pk>(\d+))/raw/$',
        NewsletterRawDetailView.as_view(),
        name="newsletter_raw_detail"),

    url(r'^(?:(?P<slug>(\w+))/)?unsubscribe/$',
        NewsletterListUnsubscribeView.as_view(),
        name="newsletter_list_unsubscribe"),

    url(r'^subscribe/done/$',
        NewsletterListSubscribeDoneView.as_view(),
        name="newsletter_list_subscribe_done"),

    url(r'^unsubscribe/(?:(?P<slug>(\w+))/)?done/$',
        NewsletterListUnsubscribeDoneView.as_view(),
        name="newsletter_list_unsubscribe_done"),

    url(r'^(?P<slug>(\w+))/(?:(?P<lang>(\w+))/)?(?:(?P<page>(\d+))/)?$',
        NewsletterListView.as_view(),
        name="newsletter_list"),
]
