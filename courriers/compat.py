import django

from django.conf import settings

__all__ = ['update_fields', 'get_user_model']

# Django 1.5+ compatibility
if django.VERSION >= (1, 5):
    update_fields = lambda instance, fields: instance.save(update_fields=fields)

    from django.contrib.auth import get_user_model
else:
    update_fields = lambda instance, fields: instance.save()

    def get_user_model():
        from django.contrib.auth.models import User

        return User

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
