from __future__ import absolute_import, unicode_literals

from mailjet_rest import Client

from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string

from ..settings import (
    MAILJET_API_KEY,
    DEFAULT_FROM_EMAIL,
    DEFAULT_FROM_NAME,
    MAILJET_API_SECRET_KEY,
    PRE_PROCESSORS,
)
from .campaign import CampaignBackend
from ..utils import load_class


class MailjetRESTBackend(CampaignBackend):
    def __init__(self):
        if not MAILJET_API_KEY:
            raise ImproperlyConfigured(
                "Please specify your MAILJET API key in Django settings"
            )

        if not MAILJET_API_SECRET_KEY:
            raise ImproperlyConfigured(
                "Please specify your MAILJET API SECRET key in Django settings"
            )

        self.client = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET_KEY))

    def _send_campaign(self, newsletter, list_id, segment_id=None):
        subject = newsletter.name

        options = {
            "Subject": subject,
            "ContactsListID": list_id,
            "Locale": "en",
            "SenderEmail": DEFAULT_FROM_EMAIL,
            "Sender": DEFAULT_FROM_NAME,
            "SenderName": DEFAULT_FROM_NAME,
            "Title": subject,
        }

        if segment_id:
            options["SegmentationID"] = segment_id

        context = {
            "object": newsletter,
            "items": newsletter.items.select_related("newsletter"),
            "options": options,
        }

        html = render_to_string("courriers/newsletter_raw_detail.html", context)
        text = render_to_string("courriers/newsletter_raw_detail.txt", context)

        for pre_processor in PRE_PROCESSORS:
            html = load_class(pre_processor)(html)

        res = self.client.campaigndraft.create(data=options)

        result = res.json()

        campaign_id = result["Data"][0]["ID"]

        data = {"Html-part": html, "Text-part": text}

        self.client.campaigndraft_detailcontent.create(id=campaign_id, data=data)
        self.client.campaigndraft_send.create(id=campaign_id)

    def subscribe(self, list_id, email, lang=None, user=None):
        data = {"Action": "addforce", "Contacts": [{"Email": email}]}

        self.client.contactslist_ManageManyContacts.create(id=list_id, data=data)

    def unsubscribe(self, list_id, email, lang=None, user=None):
        data = {"Action": "unsub", "Contacts": [{"Email": email}]}

        self.client.contactslist_ManageManyContacts.create(id=list_id, data=data)
