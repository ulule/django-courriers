from django.contrib import admin

from .models import Newsletter, NewsletterItem, NewsletterSubscriber

admin.site.register(Newsletter)
admin.site.register(NewsletterItem)
admin.site.register(NewsletterSubscriber)