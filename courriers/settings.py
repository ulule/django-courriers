from django.conf import settings


BACKEND_CLASS = getattr(settings, 'COURRIERS_BACKEND', 'courriers.backends.simple.SimpleBackend')

MAILCHIMP_API_KEY = getattr(settings, 'COURRIERS_MAILCHIMP_API_KEY', '')

MAILCHIMP_LIST_NAME = getattr(settings, 'COURRIERS_MAILCHIMP_LIST_NAME', 'Courriers')

DEFAULT_FROM_EMAIL = getattr(settings, 'COURRIERS_DEFAULT_FROM_EMAIL', 'noreply@ulule.com')

DEFAULT_FROM_NAME = getattr(settings, 'COURRIERS_DEFAULT_FROM_NAME', 'Ulule')