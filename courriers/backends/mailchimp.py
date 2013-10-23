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
        self.global_list_id = self.get_global_list_id()


    def get_global_list_id(self):
        lists = self.mc.lists.list()

        for l in lists['data']:
            if l['name'] == "Courriers":
                return l['id']
        return None


    def get_lang_list_id(self, lang):
        lists = self.mc.lists.list()

        list_name = "Courriers_%s" % lang

        for l in lists['data']:
            if l['name'] == list_name:
                return l['id']
        return None


    def register(self, email, lang=None, user=None):
        super(MailchimpBackend, self).register(email, lang, user)

        self.mc_subscribe(self.global_list_id, email)       

        if lang:
            list_id = self.get_lang_list_id(lang)
        
            self.mc_subscribe(list_id, email) 


    def unregister(self, email, user=None):
        super(MailchimpBackend, self).unregister(email, user)

        if self.exists(email):
            self.mc_unsubscribe(self.global_list_id, email)

            subscriber = self.model.objects.get(email=email)

            if subscriber.lang:
                list_id = self.get_lang_list_id(subscriber.lang)

                self.mc_unsubscribe(list_id, email)


    def mc_subscribe(self, list_id, email):
        self.mc.lists.subscribe(list_id, {'email':email}, merge_vars=None, 
                                email_type='html', double_optin=True, update_existing=False, 
                                replace_interests=True, send_welcome=False)


    def mc_unsubscribe(self, list_id, email):
        self.mc.lists.unsubscribe(list_id, {'email':email}, delete_member=False, 
                                send_goodbye=False, send_notify=False)


    def create_campaign(self, newsletter):

        options = {
           'list_id': self.global_list_id,
           'subject': newsletter.name,
           'from_email': settings.DEFAULT_FROM_EMAIL,
        }

        content = {
            'html': render_to_string('courriers/newsletterraw_detail.html', {
                        'object': newsletter,
                    })
        }

        campaign = self.mc.campaigns.create('regular', options, content, segment_opts=None, type_opts=None)

        return campaign


    def send_mails(self, newsletter):
        campaign = self.create_campaign(newsletter)
        self.mc.campaigns.send_test(campaign.cid, ['adele@ulule.com'], 'html')