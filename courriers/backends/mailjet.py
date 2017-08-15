# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.core.exceptions import ImproperlyConfigured
from django.utils.encoding import smart_text

from .campaign import CampaignBackend
from ..settings import (MAILJET_API_KEY, MAILJET_API_SECRET_KEY,
                        DEFAULT_FROM_EMAIL, DEFAULT_FROM_NAME,
                        PRE_PROCESSORS)
from ..utils import load_class

import mailjet


class MailjetBackend(CampaignBackend):
    def __init__(self):
        if not MAILJET_API_KEY:
            raise ImproperlyConfigured('Please specify your MAILJET API key in Django settings')

        if not MAILJET_API_SECRET_KEY:
            raise ImproperlyConfigured('Please specify your MAILJET API SECRET key in Django settings')

        self.mailjet_api = mailjet.Api(api_key=MAILJET_API_KEY, secret_key=MAILJET_API_SECRET_KEY)

    @cached_property
    def list_ids(self):
        return dict((l['label'], l['id']) for l in self.mailjet_api.lists.all()['lists'])

    def _subscribe(self, list_id, email):
        self.mailjet_api.lists.addcontact(
            contact=email,
            id=list_id,
            method='POST'
        )

    def _unsubscribe(self, list_id, email):
        self.mailjet_api.lists.removecontact(
            contact=email,
            id=list_id,
            method='POST'
        )

    def _send_campaign(self, newsletter, list_id):
        options = {
            'method': 'POST',
            'subject': smart_text(newsletter.name).encode('utf-8'),
            'list_id': list_id,
            'lang': 'en',
            'from': DEFAULT_FROM_EMAIL,
            'from_name': DEFAULT_FROM_NAME,
            'footer': 'default'
        }

        html = render_to_string('courriers/newsletter_raw_detail.html', {
            'object': newsletter,
            'items': newsletter.items.select_related('newsletter'),
            'options': options
        })

        campaign = self.mailjet_api.message.createcampaign(**options)

        for pre_processor in PRE_PROCESSORS:
            html = load_class(pre_processor)(html)

        extra = {
            'method': 'POST',
            'id': campaign['campaign']['id'],
            'html': smart_text(html).encode('utf-8'),
            'text': smart_text(render_to_string('courriers/newsletter_raw_detail.txt', {
                'object': newsletter,
                'items': newsletter.items.select_related('newsletter'),
                'options': options
            })).encode('utf-8')
        }

        self.mailjet_api.message.sethtmlcampaign(**extra)

        self.mailjet_api.message.sendcampaign(**{
            'method': 'POST',
            'id': campaign['campaign']['id']
        })

    def _format_slug(self, *args):
        return ''.join([(u'%s' % arg).replace('-', '') for arg in args])
