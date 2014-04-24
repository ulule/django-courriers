from django.conf import settings
from django.test.simple import DjangoTestSuiteRunner as BaseDjangoTestSuiteRunner


class DjangoTestSuiteRunner(BaseDjangoTestSuiteRunner):
    def setup_test_environment(self, *args, **kwargs):
        settings.CELERY_ALWAYS_EAGER = True
        settings.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

        super(DjangoTestSuiteRunner, self).setup_test_environment(*args,
                                                                  **kwargs)
