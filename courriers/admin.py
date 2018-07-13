from django.contrib import admin
from django.conf.urls import url
from django import forms
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import Newsletter, NewsletterItem, NewsletterList, NewsletterSegment


class NewsletterItemInline(admin.TabularInline):
    model = NewsletterItem


class NewsletterAdminForm(forms.ModelForm):
    def clean(self, *args, **kwargs):
        segment = self.cleaned_data.get("newsletter_segment")
        newsletter_list = self.cleaned_data.get("newsletter_list")

        if (
            segment
            and newsletter_list
            and segment.newsletter_list_id != newsletter_list.pk
        ):
            self.add_error(
                "newsletter_segment",
                "The segment is not attached to this newsletter list",
            )

    class Meta:
        model = Newsletter
        exclude = ()


class NewsletterAdmin(admin.ModelAdmin):
    change_form_template = "admin/courriers/newsletter/change_form.html"

    list_display = (
        "name",
        "headline",
        "published_at",
        "status",
        "newsletter_list_link",
    )
    list_filter = ("published_at", "status")
    inlines = [NewsletterItemInline]
    form = NewsletterAdminForm

    def get_queryset(self, request):
        return (
            super(NewsletterAdmin, self)
            .get_queryset(request)
            .select_related("newsletter_list")
        )

    def get_urls(self):
        urls = super(NewsletterAdmin, self).get_urls()
        my_urls = [
            url(
                r"^send/(?P<newsletter_id>(\d+))/$",
                self.send_newsletter,
                name="send_newsletter",
            )
        ]
        return my_urls + urls

    def send_newsletter(self, request, newsletter_id):
        from courriers.backends import get_backend

        backend_klass = get_backend()
        backend = backend_klass()

        newsletter = get_object_or_404(Newsletter, pk=newsletter_id)
        backend.send_mails(newsletter)

        self.message_user(request, _('The newsletter "%s" has been sent.') % newsletter)
        return HttpResponseRedirect(
            reverse("admin:courriers_newsletter_change", args=(newsletter.id,))
        )

    def newsletter_list_link(self, obj):
        url = reverse(
            "admin:courriers_newsletterlist_change", args=(obj.newsletter_list.id,)
        )
        return '<a href="%(url)s">%(name)s</a>' % {
            "url": url,
            "name": obj.newsletter_list.name,
        }

    newsletter_list_link.allow_tags = True


class NewsletterListAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")


class NewsletterSegmentAdmin(admin.ModelAdmin):
    list_display = ("name", "newsletter_list", "lang")


admin.site.register(Newsletter, NewsletterAdmin)
admin.site.register(NewsletterList, NewsletterListAdmin)
admin.site.register(NewsletterSegment, NewsletterSegmentAdmin)
