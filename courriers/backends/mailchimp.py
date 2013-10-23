# -*- coding: utf-8 -*-
from __future__ import absolute_import

from courriers.backends.simple import SimpleBackend
from courriers.models import NewsletterSubscriber
from courriers.tests.temp import MAILCHIMP_APIKEY

from django.template.loader import render_to_string
from django.conf import settings

from mailchimp import Mailchimp


class MailchimpBackend(SimpleBackend):
    model = NewsletterSubscriber

    def __init__(self):
        self.mc = Mailchimp(MAILCHIMP_APIKEY, True) # TODO : load from user settings
        self.list_id = self.get_list_id()


    def get_list_id(self):
        lists = self.mc.lists.list()

        for l in lists['data']:
            if l['name'] == "Courriers":
                return l['id']
        return None


    def register(self, email, user=None):
        super(MailchimpBackend, self).register(email, user)
        
        self.mc.lists.subscribe(self.list_id, {'email':email}, merge_vars=None, 
            email_type='html', double_optin=True, update_existing=False, 
            replace_interests=True, send_welcome=False)


    def unregister(self, email, user=None):
        super(MailchimpBackend, self).unregister(email, user)

        self.mc.lists.unsubscribe(self.list_id, {'email':email}, delete_member=False, 
            send_goodbye=False, send_notify=False)


    def create_campaign(self, newsletter):
        # TODO : Set tokens for subscribers

        options = {
           'list_id': self.list_id,
           'subject': newsletter.name,
           'from_email': settings.DEFAULT_FROM_EMAIL,
           'from_name': 'Ulule',
        }

        content = {
            'html': render_to_string('courriers/newsletterraw_detail.html', {
                        'object': newsletter,
                    })
        }

        self.mc.campaigns.create('regular', options, content, segment_opts=None, type_opts=None)


    def send_mails(self, newsletter):
        #TODO : Send campaign
        pass