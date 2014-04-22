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

        unsubscribed_users = NewsletterSubscriber.objects.using(self.connection).filter(is_unsubscribed=True)

        count_diff = 0

        for u in unsubscribed_users:
            print "Contact: %s" % u.email

            response = backend.mailjet_api.contact.infos(contact=u.email)
            if 'lists' in response:
                for l in response['lists']:
                    if not l['unsub']:
                        count_diff += 1
                        backend.unregister(u.email)
                        print "Unsubscribe user: %s" % u.email
                        break

        print "%s users were unsubscribed from your website but not from Mailjet" % count_diff
