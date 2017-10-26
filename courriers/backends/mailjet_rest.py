from __future__ import absolute_import, unicode_literals

from mailjet_rest import Client

from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import cached_property
from django.template.loader import render_to_string

from ..settings import (MAILJET_API_KEY,
                        DEFAULT_FROM_EMAIL, DEFAULT_FROM_NAME,
                        MAILJET_CONTACTSLIST_LIMIT,
                        MAILJET_API_SECRET_KEY,
                        PRE_PROCESSORS)
from .campaign import CampaignBackend
from ..utils import load_class


class MailjetRESTBackend(CampaignBackend):
    def __init__(self):
        if not MAILJET_API_KEY:
            raise ImproperlyConfigured('Please specify your MAILJET API key in Django settings')

        if not MAILJET_API_SECRET_KEY:
            raise ImproperlyConfigured('Please specify your MAILJET API SECRET key in Django settings')

        self.client = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET_KEY))

    @cached_property
    def list_ids(self):
        results = self.client.contactslist.get(filters={'Limit': MAILJET_CONTACTSLIST_LIMIT}).json()

        return dict((l['Name'], l['ID']) for l in results['Data'])

    def _subscribe(self, list_id, email):
        data = {
            'Action': 'addforce',
            'Contacts': [
                {
                    'Email': email,
                }
            ]
        }

        self.client.contactslist_ManageManyContacts.create(id=list_id, data=data)

    def _unsubscribe(self, list_id, email):
        data = {
            'Action': 'unsub',
            'Contacts': [
                {
                    'Email': email,
                }
            ]
        }

        self.client.contactslist_ManageManyContacts.create(id=list_id, data=data)

    def _format_slug(self, *args):
        return ''.join([(u'%s' % arg).replace('-', '') for arg in args])

    def _send_campaign(self, newsletter, list_id):
        subject = newsletter.name

        options = {
            'Subject': subject,
            'ContactsListID': list_id,
            'Locale': 'en',
            'SenderEmail': DEFAULT_FROM_EMAIL,
            'Sender': DEFAULT_FROM_NAME,
            'SenderName': DEFAULT_FROM_NAME,
            'Title': subject,
        }

        context = {
            'object': newsletter,
            'items': newsletter.items.select_related('newsletter'),
            'options': options
        }

        html = render_to_string('courriers/newsletter_raw_detail.html', context)
        text = render_to_string('courriers/newsletter_raw_detail.txt', context)

        for pre_processor in PRE_PROCESSORS:
            html = load_class(pre_processor)(html)

        res = self.client.campaigndraft.create(data=options)

        result = res.json()

        campaign_id = result['Data'][0]['ID']

        data = {
            'Html-part': html,
            'Text-part': text
        }

        self.client.campaigndraft_detailcontent.create(id=campaign_id, data=data)
        self.client.campaigndraft_send.create(id=campaign_id)
