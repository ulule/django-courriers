import django

from django.conf import settings

__all__ = ['update_fields', 'User']

# Django 1.5+ compatibility
if django.VERSION >= (1, 5):
    update_fields = lambda instance, fields: instance.save(update_fields=fields)

    if django.VERSION >= (1, 7):
        from django.apps import apps

        if apps.ready:
            from django.contrib.auth import get_user_model
            User = get_user_model()
    else:
        from django.contrib.auth import get_user_model
        User = get_user_model()
else:
    update_fields = lambda instance, fields: instance.save()

    from django.contrib.auth.models import User

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
