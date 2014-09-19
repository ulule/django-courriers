import django

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

SITE_ID = 1
DEBUG = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'courriers',
    'courriers.tests',
]

SECRET_KEY = 'blabla'

ROOT_URLCONF = 'courriers.urls'

try:
    from .temp import *
except ImportError:
    pass


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

if django.VERSION <= (1, 6):
    TEST_RUNNER = 'discover_runner.DiscoverRunner'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'stream': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['stream'],
            'level': 'DEBUG',
            'propagate': True,
        },

        'courriers': {
            'handlers': ['stream'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
