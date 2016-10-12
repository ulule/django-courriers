from courriers.utils import load_class

from courriers import settings


NewsletterList = load_class(settings.NEWSLETTERLIST_MODEL)

Newsletter = load_class(settings.NEWSLETTER_MODEL)

NewsletterItem = load_class(settings.NEWSLETTERITEM_MODEL)

NewsletterSubscriber = load_class(settings.NEWSLETTERSUBSCRIBER_MODEL)
