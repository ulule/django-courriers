import logging

from courriers.settings import FAIL_SILENTLY, DEFAULT_FROM_EMAIL, DEFAULT_FROM_NAME

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import translation

from .simple import SimpleBackend

logger = logging.getLogger("courriers")


class CampaignBackend(SimpleBackend):
    def send_mails(self, newsletter):
        if not newsletter.is_online():
            raise Exception("This newsletter is not online. You can't send it.")

        nl_list = newsletter.newsletter_list
        nl_segment = newsletter.newsletter_segment
        self.send_campaign(newsletter, nl_list.list_id, nl_segment.segment_id)

    def _format_slug(self, *args):
        raise NotImplementedError

    def send_campaign(self, newsletter, list_id, segment_id):
        if not DEFAULT_FROM_EMAIL:
            raise ImproperlyConfigured(
                "You have to specify a DEFAULT_FROM_EMAIL in Django settings."
            )
        if not DEFAULT_FROM_NAME:
            raise ImproperlyConfigured(
                "You have to specify a DEFAULT_FROM_NAME in Django settings."
            )

        old_language = translation.get_language()
        language = newsletter.newsletter_segment.lang or settings.LANGUAGE_CODE

        translation.activate(language)

        try:
            self._send_campaign(newsletter, list_id, segment_id=segment_id)
        except Exception as e:
            logger.exception(e)

            if not FAIL_SILENTLY:
                raise e
        else:
            newsletter.sent = True
            newsletter.save(update_fields=("sent",))

        translation.activate(old_language)

    def subscribe(self, email, list_id):
        pass

    def unsubscribe(self, email, list_id):
        pass
