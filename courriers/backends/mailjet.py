# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.utils.functional import cached_property

from .simple import SimpleBackend
from ..models import NewsletterSubscriber
from ..settings import (MAILJET_API_KEY, MAILJET_API_SECRET_KEY,
                        DEFAULT_FROM_EMAIL, DEFAULT_FROM_NAME,
                        PRE_PROCESSORS)
from ..utils import load_class
from ..compat import update_fields

import mailjet


class MailjetBackend(SimpleBackend):
    model = NewsletterSubscriber

    def __init__(self):
        if not MAILJET_API_KEY:
            raise Exception(_('Please specify your MAILJET API key in Django settings'))
        if not MAILJET_API_SECRET_KEY:
            raise Exception(_('Please specify your MAILJET API SECRET key in Django settings'))

        self.mailjet_api = mailjet.Api(api_key=MAILJET_API_KEY, secret_key=MAILJET_API_SECRET_KEY)

    @cached_property
    def list_ids(self):
        return dict((l['name'], l['id']) for l in self.mailjet_api.lists.all()['lists'])

    def create_list(self, label, name):
        try:
            self.mailjet_api.lists.create(
                label=label,
                name=name,
                method='POST'
            )
        except Exception, e:
            print 'Mailjet response: %r, %r' % (e, e.read())

    def delete_list(self, list_id):
        try:
            self.mailjet_api.lists.delete(
                id=list_id,
                method='POST'
            )
        except Exception, e:
            print 'Mailjet response: %r, %r' % (e, e.read())

    def register(self, email, newsletter_list, lang=None, user=None):
        super(MailjetBackend, self).register(email, newsletter_list, lang=lang, user=user)

        list_ids = self.list_ids

        self.mj_subscribe(list_ids[newsletter_list.slug], email)

        if lang:
            key = "%s%s" % (newsletter_list.slug, lang.upper())

            if not key in list_ids:
                raise Exception(_('List %s does not exist') % key)

            self.mj_subscribe(list_ids[key], email)

    def unregister(self, email, newsletter_list=None, user=None):
        list_ids = self.list_ids

        if newsletter_list:
            super(MailjetBackend, self).unregister(email, newsletter_list, user=user)

            list_ids = self.list_ids

            ids = [list_ids[newsletter_list.slug]]

            if newsletter_list.languages:
                for lang in newsletter_list.languages:
                    slug = u'%s%s' % (newsletter_list.slug, lang.upper())
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
        except Exception, e:
            print 'Mailjet response: %r, %r' % (e, e.read())

    def mj_unsubscribe(self, list_id, email):
        try:
            self.mailjet_api.lists.removecontact(
                contact=email,
                id=list_id,
                method='POST'
            )
        except Exception, e:
            print '2 Mailjet response: %r, %r' % (e, e.read())

    def send_campaign(self, newsletter, dict_list):

        if not DEFAULT_FROM_EMAIL:
            raise Exception(_("You have to specify a DEFAULT_FROM_EMAIL in Django settings."))
        if not DEFAULT_FROM_NAME:
            raise Exception(_("You have to specify a DEFAULT_FROM_NAME in Django settings."))

        options = {
            'method': 'POST',
            'subject': newsletter.name,
            'list_id': dict_list['id'],
            'lang': settings.LANGUAGE_CODE,
            'from': DEFAULT_FROM_EMAIL,
            'from_name': DEFAULT_FROM_NAME,
            'footer': 'default'
        }

        if 'lang' in dict_list:
            options['lang'] = dict_list['lang']

        campaign = self.mailjet_api.message.createcampaign(**options)

        extra = {
            'method': 'POST',
            'id': campaign.id,
            'html': render_to_string('courriers/newsletter_raw_detail.html', {
                'object': newsletter,
                'items': newsletter.items.all().prefetch_related('newsletter')
            }),
            'text': ''
        }

        for pre_processor in PRE_PROCESSORS:
            extra['html'] = load_class(pre_processor)(extra['html'])

        self.mailjet_api.message.sethtmlcampaign(**extra)

        self.mailjet_api.message.sendcampaign({
            'method': 'POST',
            'id': campaign.id
        })

        newsletter.sent = True
        update_fields(newsletter, fields=('sent', ))

    def send_mails(self, newsletter):
        if not newsletter.is_online():
            raise Exception(_("This newsletter is not online. You can't send it."))

        list_ids = self.list_ids
        lists = []

        if newsletter.languages:
            for lang in newsletter.languages:
                slug = u'%s%s' % (newsletter.newsletter_list.slug, lang.upper())
                if slug in list_ids:
                    lists.append({
                        'id': list_ids[slug],
                        'lang': lang.upper()
                    })
        else:
            lists.append({
                'id': list_ids[newsletter.newsletter_list.slug],
            })

        for dict_list in lists:
            self.send_campaign(newsletter, dict_list)
