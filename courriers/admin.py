from django.contrib import admin
from django.conf.urls import url
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from .models import Newsletter, NewsletterItem, NewsletterSubscriber, NewsletterList


class NewsletterItemInline(admin.TabularInline):
    model = NewsletterItem


class NewsletterAdmin(admin.ModelAdmin):
    change_form_template = 'admin/courriers/newsletter/change_form.html'

    list_display = ('name', 'headline', 'published_at', 'status', 'newsletter_list',)
    list_filter = ('published_at', 'status',)
    inlines = [NewsletterItemInline]

    def get_urls(self):
        urls = super(NewsletterAdmin, self).get_urls()
        my_urls = [
            url(r'^send/(?P<newsletter_id>(\d+))/$',
                self.send_newsletter,
                name="send_newsletter")
        ]
        return my_urls + urls

    def send_newsletter(self, request, newsletter_id):
        from courriers.backends import get_backend

        backend_klass = get_backend()
        backend = backend_klass()

        newsletter = get_object_or_404(Newsletter, pk=newsletter_id)
        backend.send_mails(newsletter)

        self.message_user(request, _('The newsletter "%s" has been sent.') % newsletter)
        return HttpResponseRedirect(reverse('admin:courriers_newsletter_change', args=(newsletter.id,)))


class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'user', 'lang', 'is_unsubscribed',)
    list_filter = ('is_unsubscribed',)


class NewsletterListAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at',)


admin.site.register(Newsletter, NewsletterAdmin)
admin.site.register(NewsletterSubscriber, NewsletterSubscriberAdmin)
admin.site.register(NewsletterList, NewsletterListAdmin)
