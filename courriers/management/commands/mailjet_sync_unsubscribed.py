from django.core.management.base import BaseCommand
from django.db import DEFAULT_DB_ALIAS

from optparse import make_option


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--connection',
                    action='store',
                    dest='connection',
                    default=DEFAULT_DB_ALIAS,
                    ),
    )

    def handle(self, *args, **options):
        from courriers.backends import get_backend
        from courriers.models import NewsletterSubscriber

        self.connection = options.get('connection')

        backend_klass = get_backend()

        backend = backend_klass()

        unsubscribed_users = (NewsletterSubscriber.objects.using(self.connection)
                                                          .filter(is_unsubscribed=True)
                                                          .values_list('email', flat=True)
                                                          .order_by('-unsubscribed_at'))

        mailjet_contacts = backend.mailjet_api.contact.list(unsub=1)

        mailjet_users = [contact['email'] for contact in mailjet_contacts['result']]

        diff = list(set(unsubscribed_users) - set(mailjet_users))

        print "%d contacts to unsubscribe" % len(diff)

        for email in diff:
            backend.unregister(email)

            print "Unsubscribe user: %s" % email
