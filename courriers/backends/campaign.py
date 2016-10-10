import logging

from courriers.settings import FAIL_SILENTLY, DEFAULT_FROM_EMAIL, DEFAULT_FROM_NAME

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import translation

from .simple import SimpleBackend

logger = logging.getLogger('courriers')


class CampaignBackend(SimpleBackend):
    def send_mails(self, newsletter):
        if not newsletter.is_online():
            raise Exception("This newsletter is not online. You can't send it.")

        list_ids = self.list_ids
        ids = []

        if newsletter.languages:
            for lang in newsletter.languages:
                slug = self._format_slug(newsletter.newsletter_list.slug, lang)
                if slug in list_ids:
                    ids.append(list_ids[slug])
        else:
            ids.append(list_ids[newsletter.newsletter_list.slug])

        for list_id in ids:
            self.send_campaign(newsletter, list_id)

    def _format_slug(self, *args):
        raise NotImplementedError

    @property
    def list_ids(self):
        raise NotImplementedError

    def register(self, email, newsletter_list, lang=None, user=None):
        super(CampaignBackend, self).register(email, newsletter_list, lang=lang, user=user)

        list_ids = self.list_ids

        keys = [self._format_slug(newsletter_list.slug), ]

        if lang:
            keys.append(self._format_slug(newsletter_list.slug, lang))

        for key in keys:
            if key not in list_ids:

                message = 'List %s does not exist' % key

                if not FAIL_SILENTLY:
                    raise Exception(message)

                logger.error(message)
            else:
                try:
                    self._subscribe(list_ids[key], email)
                except Exception as e:
                    logger.exception(e)

                    if not FAIL_SILENTLY:
                        raise e

    def unregister(self, email, newsletter_list=None, user=None, lang=None):
        if newsletter_list:
            super(CampaignBackend, self).unregister(email, newsletter_list, user=user, lang=lang)

            list_ids = self.list_ids

            keys = [self._format_slug(newsletter_list.slug), ]

            if newsletter_list.languages:
                for lang in newsletter_list.languages:
                    keys.append(self._format_slug(newsletter_list.slug, lang))

            for key in keys:
                if key not in list_ids:
                    message = 'List %s does not exist' % key

                    if not FAIL_SILENTLY:
                        raise Exception(message)

                    logger.error(message)
                else:
                    try:
                        self._unsubscribe(list_ids[key], email)
                    except Exception as e:
                        logger.exception(e)

                        if not FAIL_SILENTLY:
                            raise e
        else:
            for subscriber in self.all(email, user=user):
                self.unregister(email, subscriber.newsletter_list, user=user)

    def send_campaign(self, newsletter, list_id):
        if not DEFAULT_FROM_EMAIL:
            raise ImproperlyConfigured("You have to specify a DEFAULT_FROM_EMAIL in Django settings.")
        if not DEFAULT_FROM_NAME:
            raise ImproperlyConfigured("You have to specify a DEFAULT_FROM_NAME in Django settings.")

        old_language = translation.get_language()

        language = settings.LANGUAGE_CODE

        if len(newsletter.languages) == 1:
            language = newsletter.languages[0]

        translation.activate(language)

        try:
            self._send_campaign(newsletter, list_id)
        except Exception as e:
            logger.exception(e)

            if not FAIL_SILENTLY:
                raise e
        else:
            newsletter.sent = True
            newsletter.save(update_fields=('sent', ))

        translation.activate(old_language)
