from django.conf.urls.defaults import patterns, url

from .views import NewsletterListView, NewsletterDetailView, NewsletterRawDetailView


urlpatterns = patterns(
	'',
    url(r'^$', NewsletterListView.as_view(), name="newsletter_list"),
    url(r'^(?P<pk>(\d+))/$', NewsletterDetailView.as_view(), name="newsletter_detail"),
    url(r'^(?P<pk>(\d+))/raw/$', NewsletterRawDetailView.as_view(), name="newsletterraw_detail"),
)
