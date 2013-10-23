from django.conf import settings


BACKEND_CLASS = getattr(settings, 'COURRIERS_BACKEND', 'courriers.backends.simple.SimpleBackend')