# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.template.loader import render_to_string

from courriers.backends.simple import SimpleBackend
from courriers.models import Newsletter, NewsletterSubscriber
from courriers.settings import MAILCHIMP_API_KEY, MAILCHIMP_LIST_NAME, DEFAULT_FROM_EMAIL, DEFAULT_FROM_NAME

from mailchimp import Mailchimp


class MailchimpBackend(SimpleBackend):
    model = NewsletterSubscriber
    mailchimp_class = Mailchimp

    def __init__(self):
        self.mc = self.mailchimp_class(MAILCHIMP_API_KEY, True)


    def get_list_ids(self, lang=None):
        lists = self.mc.lists.list()

        ids = []
        names = [MAILCHIMP_LIST_NAME]

        if lang:
            names.append("%s_%s" % (MAILCHIMP_LIST_NAME, lang))

        for l in lists['data']:
            if l['name'] in names:
                ids.append(l['id'])
        return ids


    def register(self, email, lang=None, user=None):
        super(MailchimpBackend, self).register(email, lang, user)

        list_ids = self.get_list_ids(lang)

        for list_id in list_ids:
            self.mc_subscribe(list_id, email)


    def unregister(self, email, user=None):
        super(MailchimpBackend, self).unregister(email, user)

        if self.exists(email):

            subscriber = self.model.objects.get(email=email)

            list_ids = self.get_list_ids(subscriber.lang)

            for list_id in list_ids:
                self.mc_unsubscribe(list_id, email)


    def mc_subscribe(self, list_id, email):
        self.mc.lists.subscribe(list_id, {'email':email}, merge_vars=None, 
                                email_type='html', double_optin=False, update_existing=False, 
                                replace_interests=True, send_welcome=False)


    def mc_unsubscribe(self, list_id, email):
        self.mc.lists.unsubscribe(list_id, {'email':email}, delete_member=False, 
                                send_goodbye=False, send_notify=False)


    def create_campaign(self, newsletter, lang):

        list_ids = self.get_list_ids(lang)

        for list_id in list_ids:

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

            return campaign


    def send_mails(self, newsletter=None, lang=None):

        newsletters = Newsletter.objects.filter(status=Newsletter.STATUS_ONLINE)

        if newsletter:
            newsletters = [newsletter]
        elif lang:
            newsletters = Newsletter.objects.filter(status=Newsletter.STATUS_ONLINE, lang=lang)


        for n in newsletters:
            campaign = self.create_campaign(n, n.lang)
            self.mc.campaigns.send_test(campaign['id'])