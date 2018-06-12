from __future__ import absolute_import

from celery.task import task


@task(bind=True)
def subscribe(self, email, newsletter_list_id, user_id=None, **kwargs):
    from courriers.backends import get_backend
    from courriers.models import NewsletterList
    from courriers import signals

    from django.contrib.auth import get_user_model

    User = get_user_model()

    backend = get_backend()()

    newsletter_list = None

    if newsletter_list_id:
        newsletter_list = NewsletterList.objects.get(pk=newsletter_list_id)

    user = None

    if user_id is not None:
        user = User.objects.get(pk=user_id)
    else:
        user = User.objects.filter(email=email).last()

    if user:
        signals.subscribed.send(sender=User, user=user, newsletter_list=newsletter_list)

    else:
        try:
            backend.subscribe(newsletter_list.list_id, email)
        except Exception as e:
            raise self.retry(exc=e, countdown=60)


@task(bind=True)
def unsubscribe(self, email, newsletter_list_id=None, user_id=None, **kwargs):
    from courriers.backends import get_backend
    from courriers.models import NewsletterList
    from courriers import signals

    from django.contrib.auth import get_user_model

    User = get_user_model()

    newsletter_lists = NewsletterList.objects.all()

    if newsletter_list_id:
        newsletter_lists = NewsletterList.objects.filter(pk=newsletter_list_id)

    user = None

    if user_id is not None:
        user = User.objects.get(pk=user_id)
    else:
        user = User.objects.filter(email=email).last()

    if user:
        for newsletter_list in newsletter_lists:
            signals.unsubscribed.send(
                sender=User, user=user, newsletter_list=newsletter_list
            )
    else:
        backend = get_backend()()

        for newsletter in newsletter_lists:
            backend.unsubscribe(newsletter.list_id, email)
