# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from .simple import SimpleBackend
from ..models import NewsletterSubscriber
from ..settings import (MAILCHIMP_API_KEY,
                        DEFAULT_FROM_EMAIL, DEFAULT_FROM_NAME)

from mailchimp import Mailchimp


class MailchimpBackend(SimpleBackend):
    model = NewsletterSubscriber
    mailchimp_class = Mailchimp

    def __init__(self):
        self.mc = self.mailchimp_class(MAILCHIMP_API_KEY, True)

    def get_list_ids(self):
        return dict((l['name'], l['id']) for l in self.mc.lists.list()['data'])

    def register(self, email, newsletter_list, lang=None, user=None):
        super(MailchimpBackend, self).register(email, newsletter_list, lang=lang, user=user)

        list_ids = self.get_list_ids()

        self.mc_subscribe(list_ids[newsletter_list.slug], email)

        if lang:
            key = "%s_%s" % (newsletter_list.slug, lang)

            if not key in list_ids:
                raise Exception(_('List %s does not exist') % key)

            self.mc_subscribe(list_ids[key], email)

    def unregister(self, email, newsletter_list, user=None):
        super(MailchimpBackend, self).unregister(email, newsletter_list, user=user)

        if self.exists(email):
            list_ids = self.get_list_ids()

            self.mc_unsubscribe(list_ids[newsletter_list.slug], email)

            subscriber = NewsletterSubscriber.objects.get(email=email)

            if subscriber.lang:
                key = "%s_%s" % (newsletter_list.slug, subscriber.lang)
                self.mc_unsubscribe(list_ids[key], email)

    def mc_subscribe(self, list_id, email):
        self.mc.lists.subscribe(list_id, {'email': email}, merge_vars=None,
                                email_type='html', double_optin=False, update_existing=False,
                                replace_interests=True, send_welcome=False)

    def mc_unsubscribe(self, list_id, email):
        self.mc.lists.unsubscribe(list_id, {'email': email}, delete_member=False,
                                  send_goodbye=False, send_notify=False)

    def send_campaign(self, newsletter):

        lists = self.get_list_ids()

        if newsletter.lang:
            key = "%s_%s" % (newsletter.newsletter_list.slug, newsletter.lang)
        else:
            key = newsletter.newsletter_list.slug

        if not key in lists:
            raise Exception(_('List %s does not exist') % key)

        list_id = lists[key]

        if not DEFAULT_FROM_EMAIL:
            raise Exception(_("You have to specify a DEFAULT_FROM_EMAIL in settings."))
        if not DEFAULT_FROM_NAME:
            raise Exception(_("You have to specify a DEFAULT_FROM_NAME in settings."))

        options = {
            'list_id': list_id,
            'subject': newsletter.name,
            'from_email': DEFAULT_FROM_EMAIL,
            'from_name': DEFAULT_FROM_NAME
        }

        content = {
            'html': render_to_string('courriers/newsletterraw_detail.html', {
                'object': newsletter,
            })
        }

        campaign = self.mc.campaigns.create('regular', options, content, segment_opts=None, type_opts=None)

        self.mc.campaigns.send(campaign['id'])

    def send_mails(self, newsletter):
        if not newsletter.is_online():
            raise Exception(_("This newsletter is not online. You can't send it."))

        self.send_campaign(newsletter)
