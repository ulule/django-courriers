from __future__ import absolute_import
from celery.task import task


@task
def subscribe(email, newsletter_list_id, lang=None, user_id=None):
    from courriers.backends import get_backend
    from courriers.models import NewsletterList
    from courriers.compat import get_user_model

    User = get_user_model()

    backend = get_backend()()

    newsletter_list = None

    if newsletter_list_id:
        newsletter_list = NewsletterList.objects.get(pk=newsletter_list_id)

    user = None

    if user_id is not None:
        user = User.objects.get(pk=user_id)

    try:
        backend.register(email=email,
                         newsletter_list=newsletter_list,
                         lang=lang,
                         user=user)
    except Exception as e:
        raise subscribe.retry(args=[email, newsletter_list, lang, user], exc=e, countdown=30)


@task
def unsubscribe(email, newsletter_list_id=None, lang=None, user_id=None):
    from courriers.backends import get_backend
    from courriers.models import NewsletterList
    from courriers.compat import get_user_model

    User = get_user_model()

    newsletter_list = None

    if newsletter_list_id:
        newsletter_list = NewsletterList.objects.get(pk=newsletter_list_id)

    user = None

    if user_id is not None:
        user = User.objects.get(pk=user_id)

    backend = get_backend()()

    try:
        backend.unregister(email=email,
                           newsletter_list=newsletter_list,
                           lang=lang,
                           user=user)
    except Exception as e:
        raise unsubscribe.retry(args=[email, newsletter_list, lang, user], exc=e, countdown=30)
