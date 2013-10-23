# -*- coding: utf-8 -*-
from __future__ import absolute_import

from courriers.backends.base import BaseBackend
from courriers.models import NewsletterSubscriber

from django.template.loader import render_to_string

from mailchimp import Mailchimp


class Backend(BaseBackend):
    model = NewsletterSubscriber

    def __init__(self):
        self.mc = Mailchimp(settings.MAILCHIMP_APIKEY, True)
        self.list_id = self.get_list_id()


    def get_list_id(self):
        lists = self.mc.lists.list()

        for l in lists['data']:
            if l['name'] == "Ulule Newsletter":
                return l['id']
        return None


    def subscribe(self, email, user=None):
        if user:
            new_subscriber = self.model(email=email, user=user)
        else:
            new_subscriber = self.model(email=email)
        new_subscriber.save()


    def register(self, email, user=None):
        if not self.exists(email):
            self.subscribe(email)

            semail = {
                'email': email,
                'euid': 1,
                'leid': 1,
            }
            
            self.mc.lists.subscribe(self.list_id, semail, merge_vars=None, 
                email_type='html', double_optin=True, update_existing=False, 
                replace_interests=True, send_welcome=False)


    def unregister(self, email, user=None):
        if self.exists(email):
            self.model.objects.get(email=email).unsubscribe()

            semail = {
                'email': email,
                'euid': 1,
                'leid': 1,
            }

            self.mc.lists.unsubscribe(self.list_id, semail, delete_member=False, 
                send_goodbye=False, send_notify=False)


    def exists(self, email, user=None):
        return self.model.objects.filter(email=email).exists()


    def create_campaign(self, newsletter):
        # TODO : Set tokens for subscribers

        options = {
           'list_id': self.list_id,
           'subject': newsletter.name,
           'from_email': 'adele@ulule.com',
           'from_name': 'Adèle Ulule',
           'to_name': 'Ululer',
        }

        content = {
            'html': render_to_string('courriers/newsletterraw_detail.html', {
                        'object': newsletter,
                        'subscriber': ''
                    }),
        }

        self.mc.campaigns.create('regular', options, content, segment_opts=None, type_opts=None)


    def send_mails(self, newsletter):
        #TODO : Send campaign
        pass