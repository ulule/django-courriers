# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.utils.functional import cached_property
from django.core.exceptions import ImproperlyConfigured

from .simple import SimpleBackend
from ..settings import (MAILJET_API_KEY, MAILJET_API_SECRET_KEY,
                        DEFAULT_FROM_EMAIL, DEFAULT_FROM_NAME,
                        PRE_PROCESSORS, FAIL_SILENTLY)
from ..utils import load_class
from ..compat import update_fields

import mailjet

logger = logging.getLogger('courriers')


class MailjetBackend(SimpleBackend):
    def __init__(self):
        if not MAILJET_API_KEY:
            raise ImproperlyConfigured(_('Please specify your MAILJET API key in Django settings'))

        if not MAILJET_API_SECRET_KEY:
            raise ImproperlyConfigured(_('Please specify your MAILJET API SECRET key in Django settings'))

        self.mailjet_api = mailjet.Api(api_key=MAILJET_API_KEY, secret_key=MAILJET_API_SECRET_KEY)

    @cached_property
    def list_ids(self):
        return dict((l['label'], l['id']) for l in self.mailjet_api.lists.all()['lists'])

    def create_list(self, label, name):
        try:
            self.mailjet_api.lists.create(
                label=label,
                name=name,
                method='POST'
            )
        except Exception as e:
            logger.error(e)

            if not FAIL_SILENTLY:
                raise e

    def delete_list(self, list_id):
        try:
            self.mailjet_api.lists.delete(
                id=list_id,
                method='POST'
            )
        except Exception as e:
            logger.error(e)

            if not FAIL_SILENTLY:
                raise e

    def list_contacts(self, list_id):
        return self.mailjet_api.lists.contacts(
            id=list_id,
        )

    def register(self, email, newsletter_list, lang=None, user=None):
        super(MailjetBackend, self).register(email, newsletter_list, lang=lang, user=user)

        list_ids = self.list_ids
        self.mj_subscribe(list_ids[newsletter_list.slug], email)

        if lang:
            key = self._format_slug(newsletter_list.slug, lang)

            if not key in list_ids:
                raise Exception(_('List %s does not exist') % key)

            self.mj_subscribe(list_ids[key], email)

    def unregister(self, email, newsletter_list=None, user=None):
        if newsletter_list:
            super(MailjetBackend, self).unregister(email, newsletter_list, user=user)

            list_ids = self.list_ids

            ids = [list_ids[newsletter_list.slug]]

            if newsletter_list.languages:
                for lang in newsletter_list.languages:
                    slug = self._format_slug(newsletter_list.slug, lang)
                    ids.append(list_ids[slug])

            for lid in ids:
                self.mj_unsubscribe(lid, email)
        else:
            for subscriber in self.all(email, user=user):
                self.unregister(email, subscriber.newsletter_list, user=user)

    def mj_subscribe(self, list_id, email):
        try:
            self.mailjet_api.lists.addcontact(
                contact=email,
                id=list_id,
                method='POST'
            )
        except Exception as e:
            logger.error(e)

            if not FAIL_SILENTLY:
                raise e

    def mj_unsubscribe(self, list_id, email):
        try:
            self.mailjet_api.lists.removecontact(
                contact=email,
                id=list_id,
                method='POST'
            )
        except Exception as e:
            logger.error(e)

            if not FAIL_SILENTLY:
                raise e

    def send_campaign(self, newsletter, list_id):

        if not DEFAULT_FROM_EMAIL:
            raise ImproperlyConfigured(_("You have to specify a DEFAULT_FROM_EMAIL in Django settings."))

        if not DEFAULT_FROM_NAME:
            raise ImproperlyConfigured(_("You have to specify a DEFAULT_FROM_NAME in Django settings."))

        options = {
            'method': 'POST',
            'subject': newsletter.name,
            'list_id': list_id,
            'lang': 'en',
            'from': DEFAULT_FROM_EMAIL,
            'from_name': DEFAULT_FROM_NAME,
            'footer': 'default'
        }

        try:
            campaign = self.mailjet_api.message.createcampaign(**options)
        except Exception as e:
            logger.error(e)

            if not FAIL_SILENTLY:
                raise e
        else:
            html = render_to_string('courriers/newsletter_raw_detail.html', {
                'object': newsletter,
                'items': newsletter.items.select_related('newsletter')
            })

            for pre_processor in PRE_PROCESSORS:
                html = load_class(pre_processor)(html)

            extra = {
                'method': 'POST',
                'id': campaign['campaign']['id'],
                'html': html,
                'text': render_to_string('courriers/newsletter_raw_detail.txt', {
                    'object': newsletter,
                    'items': newsletter.items.select_related('newsletter')
                })
            }

            try:
                self.mailjet_api.message.sethtmlcampaign(**extra)

                self.mailjet_api.message.sendcampaign(**{
                    'method': 'POST',
                    'id': campaign['campaign']['id']
                })
            except Exception as e:
                logger.error(e)

                if not FAIL_SILENTLY:
                    raise e
            else:
                newsletter.sent = True
                update_fields(newsletter, fields=('sent', ))

    def _format_slug(self, *args):
        return u''.join([unicode(arg).replace('-', '') for arg in args])

    def send_mails(self, newsletter):
        if not newsletter.is_online():
            raise Exception(_("This newsletter is not online. You can't send it."))

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
