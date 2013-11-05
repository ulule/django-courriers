from django.contrib import admin

from .models import Newsletter, NewsletterItem, NewsletterSubscriber


class NewsletterAdmin(admin.ModelAdmin):
    list_display = ('name', 'headline', 'lang', 'published_at', 'status',)
    list_filter = ('lang', 'published_at', 'status',)


class NewsletterItemAdmin(admin.ModelAdmin):
    list_display = ('description', 'content_type', 'newsletter',)


class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'user', 'lang', 'is_unsubscribed',)
    list_filter = ('lang', 'is_unsubscribed',)


admin.site.register(Newsletter, NewsletterAdmin)
admin.site.register(NewsletterItem, NewsletterItemAdmin)
admin.site.register(NewsletterSubscriber, NewsletterSubscriberAdmin)
