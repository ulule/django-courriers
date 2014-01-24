# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.utils.functional import cached_property

from .simple import SimpleBackend
from ..models import NewsletterSubscriber
from ..settings import (MAILCHIMP_API_KEY, PRE_PROCESSORS,
                        DEFAULT_FROM_EMAIL, DEFAULT_FROM_NAME)
from ..utils import load_class
from ..compat import update_fields

from mailchimp import Mailchimp, ListNotSubscribedError

logger = logging.getLogger('courriers')


class MailchimpBackend(SimpleBackend):
    model = NewsletterSubscriber
    mailchimp_class = Mailchimp

    def __init__(self):
        if not MAILCHIMP_API_KEY:
            raise Exception(_('Please specify your MAILCHIMP API key in Django settings'))
        self.mc = self.mailchimp_class(MAILCHIMP_API_KEY, True)

    @cached_property
    def list_ids(self):
        return dict((l['name'], l['id']) for l in self.mc.lists.list()['data'])

    def register(self, email, newsletter_list, lang=None, user=None):
        super(MailchimpBackend, self).register(email, newsletter_list, lang=lang, user=user)

        list_ids = self.list_ids

        self.mc_subscribe(list_ids[newsletter_list.slug], email)

        if lang:
            key = "%s_%s" % (newsletter_list.slug, lang)

            if not key in list_ids:
                raise Exception(_('List %s does not exist') % key)

            self.mc_subscribe(list_ids[key], email)

    def unregister(self, email, newsletter_list=None, user=None):
        if newsletter_list:
            super(MailchimpBackend, self).unregister(email, newsletter_list, user=user)

            list_ids = self.list_ids

            ids = [list_ids[newsletter_list.slug]]

            if newsletter_list.languages:
                for lang in newsletter_list.languages:
                    slug = u'%s_%s' % (newsletter_list.slug, lang)
                    ids.append(list_ids[slug])

            for lid in ids:
                try:
                    self.mc_unsubscribe(lid, email)
                except ListNotSubscribedError as e:
                    logger.error(e)
        else:
            for subscriber in self.all(email, user=user):
                self.unregister(email, subscriber.newsletter_list, user=user)

    def mc_subscribe(self, list_id, email):
        self.mc.lists.subscribe(list_id, {'email': email}, merge_vars=None,
                                email_type='html', double_optin=False, update_existing=False,
                                replace_interests=True, send_welcome=False)

    def mc_unsubscribe(self, list_id, email):
        self.mc.lists.unsubscribe(list_id, {'email': email}, delete_member=False,
                                  send_goodbye=False, send_notify=False)

    def send_campaign(self, newsletter, list_id):

        if not DEFAULT_FROM_EMAIL:
            raise Exception(_("You have to specify a DEFAULT_FROM_EMAIL in Django settings."))
        if not DEFAULT_FROM_NAME:
            raise Exception(_("You have to specify a DEFAULT_FROM_NAME in Django settings."))

        options = {
            'list_id': list_id,
            'subject': newsletter.name,
            'from_email': DEFAULT_FROM_EMAIL,
            'from_name': DEFAULT_FROM_NAME
        }

        html = render_to_string('courriers/newsletter_raw_detail.html', {
            'object': newsletter,
            'items': newsletter.items.all().prefetch_related('newsletter')
        })

        for pre_processor in PRE_PROCESSORS:
            html = load_class(pre_processor)(html)

        content = {
            'html': html
        }

        campaign = self.mc.campaigns.create('regular', options, content, segment_opts=None, type_opts=None)

        self.mc.campaigns.send(campaign['id'])

        newsletter.sent = True
        update_fields(newsletter, fields=('sent', ))

    def send_mails(self, newsletter):
        if not newsletter.is_online():
            raise Exception(_("This newsletter is not online. You can't send it."))

        list_ids = self.list_ids
        ids = []

        if newsletter.languages:
            for lang in newsletter.languages:
                slug = u'%s_%s' % (newsletter.newsletter_list.slug, lang)
                if slug in list_ids:
                    ids.append(list_ids[slug])
        else:
            ids.append(list_ids[newsletter.newsletter_list.slug])

        for list_id in ids:
            self.send_campaign(newsletter, list_id)
