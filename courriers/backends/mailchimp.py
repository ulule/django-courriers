# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import logging

from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.utils.functional import cached_property
from django.core.exceptions import ImproperlyConfigured

from .campaign import CampaignBackend
from ..settings import (MAILCHIMP_API_KEY, PRE_PROCESSORS,
                        DEFAULT_FROM_EMAIL, DEFAULT_FROM_NAME)
from ..utils import load_class

from mailchimp import Mailchimp

logger = logging.getLogger('courriers')


class MailchimpBackend(CampaignBackend):
    mailchimp_class = Mailchimp

    def __init__(self):
        if not MAILCHIMP_API_KEY:
            raise ImproperlyConfigured(_('Please specify your MAILCHIMP API key in Django settings'))
        self.mc = self.mailchimp_class(MAILCHIMP_API_KEY, True)

    @cached_property
    def list_ids(self):
        return dict((l['name'], l['id']) for l in self.mc.lists.list()['data'])

    def _subscribe(self, list_id, email):
        self.mc.lists.subscribe(list_id, {'email': email}, merge_vars=None,
                                email_type='html', double_optin=False, update_existing=False,
                                replace_interests=True, send_welcome=False)

    def _unsubscribe(self, list_id, email):
        self.mc.lists.unsubscribe(list_id, {'email': email}, delete_member=False,
                                  send_goodbye=False, send_notify=False)

    def _send_campaign(self, newsletter, list_id):
        options = {
            'list_id': list_id,
            'subject': newsletter.name,
            'from_email': DEFAULT_FROM_EMAIL,
            'from_name': DEFAULT_FROM_NAME
        }

        html = render_to_string('courriers/newsletter_raw_detail.html', {
            'object': newsletter,
            'items': newsletter.items.select_related('newsletter'),
            'options': options
        })

        for pre_processor in PRE_PROCESSORS:
            html = load_class(pre_processor)(html)

        content = {
            'html': html
        }

        campaign = self.mc.campaigns.create('regular', options, content, segment_opts=None, type_opts=None)

        self.mc.campaigns.send(campaign['id'])

    def _format_slug(self, *args):
        return u'_'.join([u'%s' % arg for arg in args])
