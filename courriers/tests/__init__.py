# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test.utils import override_settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils import timezone as datetime
from django.core import mail

from courriers.forms import SubscriptionForm
from courriers.models import Newsletter, NewsletterSubscriber



class SimpleBackendTests(TestCase):

    def setUp(self):
        from courriers.backends import get_backend

        self.backend_klass = get_backend()
        self.backend = self.backend_klass()

    def test_registration(self):
        # Subscribe

        self.backend.register('adele@ulule.com', 'FR')
        self.backend.register('adele.delamarche@gmail.com')

        subscriber = NewsletterSubscriber.objects.filter(email='adele@ulule.com', is_unsubscribed=False)
        self.assertEqual(subscriber.count(), 1)


        # Send emails

        n1 = Newsletter.objects.create(name="3000 projets finances", 
                                      published_at=datetime.now() - datetime.timedelta(hours=2),
                                      status=Newsletter.STATUS_ONLINE)

        n2 = Newsletter.objects.create(name="3000 projets finances [FR]", 
                                      published_at=datetime.now() - datetime.timedelta(hours=2),
                                      status=Newsletter.STATUS_ONLINE, lang='FR')

        n3 = Newsletter.objects.create(name="3000 projets finances [en-us]", 
                                      published_at=datetime.now() - datetime.timedelta(hours=2),
                                      status=Newsletter.STATUS_ONLINE, lang='en-us')


        if self.backend_klass.__name__ == "SimpleBackend":
            self.backend.send_mails(n1)
            self.assertEqual(len(mail.outbox), NewsletterSubscriber.objects.subscribed().count())
            out = len(mail.outbox)

            self.backend.send_mails(n2)
            self.assertEqual(len(mail.outbox) - out, NewsletterSubscriber.objects.subscribed().has_lang('FR').count())
            out = len(mail.outbox)

            self.backend.send_mails(n3)
            self.assertEqual(len(mail.outbox) - out, NewsletterSubscriber.objects.subscribed().has_lang('en-us').count())


        # Unsubscribe
        
        subscriber = NewsletterSubscriber.objects.get(email='adele@ulule.com')
        self.assertEqual(subscriber.lang, 'FR')

        subscriber2 = NewsletterSubscriber.objects.get(email='adele.delamarche@gmail.com')
        self.assertEqual(subscriber2.lang, None)


        self.backend.unregister(subscriber.email)
        self.backend.unregister(subscriber2.email)

        self.backend.unregister('florent@ulule.com') # Subscriber does not exist

        unsubscriber = NewsletterSubscriber.objects.filter(email='adele@ulule.com', is_unsubscribed=True)
        self.assertEqual(unsubscriber.count(), 1)


class MailchimpBackendTests(SimpleBackendTests):
    pass

override_settings(COURRIERS_BACKEND_CLASS='courriers.backends.mailchimp.MailchimpBackend')(MailchimpBackendTests)



class NewslettersViewsTests(TestCase):
    def setUp(self):
        Newsletter.objects.create(name='Newsletter1', published_at=datetime.now())

    def test_newsletter_list(self):
        response = self.client.get(reverse('newsletter_list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courriers/newsletter_list.html')

    def test_newsletter_detail(self):
        response = self.client.get(reverse('newsletter_detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courriers/newsletter_detail.html')

        self.assertTrue(isinstance(response.context['form'], SubscriptionForm))

    def test_newsletterraw_detail(self):
        response = self.client.get(reverse('newsletterraw_detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courriers/newsletterraw_detail.html')



class SubscribeFormTest(TestCase):
    def setUp(self):
        from courriers.backends import get_backend

        self.backend_klass = get_backend()
        self.backend = self.backend_klass()

    def test_subscription_logged_out(self):
        valid_data = {'receiver': 'adele@ulule.com'}

        form = SubscriptionForm(data=valid_data)

        self.assertTrue(form.is_valid())

        form.save()

        new_subscriber = NewsletterSubscriber.objects.filter(email=valid_data['receiver'])

        self.assertEqual(new_subscriber.count(), 1)
        self.assertNotEqual(new_subscriber.get().lang, None)

        # Test duplicate
        form2 = SubscriptionForm(data=valid_data)

        is_valid = form2.is_valid()

        self.assertEqual(is_valid, False)

        self.backend.unregister('adele@ulule.com')

    def test_subscription_logged_in(self):
        self.client.login(username='thoas', password='secret')

        valid_data = {'receiver': 'florent@ulule.com'}

        form = SubscriptionForm(data=valid_data)

        self.assertTrue(form.is_valid())

        user = User.objects.create(username='thoas')

        form.save(user)

        new_subscriber = NewsletterSubscriber.objects.filter(email=valid_data['receiver'], user=user)

        self.assertEqual(new_subscriber.count(), 1)
        self.assertNotEqual(new_subscriber.get().lang, None)

        self.backend.unregister('florent@ulule.com')


class SubscribeMailchimpFormTest(SubscribeFormTest):
    pass

override_settings(COURRIERS_BACKEND_CLASS='courriers.backends.mailchimp.MailchimpBackend')(SubscribeMailchimpFormTest)



class NewsletterModelsTest(TestCase):
    def test_navigation(self):
        n1 = Newsletter.objects.create(name='Newsletter1',
                                       status=Newsletter.STATUS_ONLINE,
                                       published_at=datetime.now() - datetime.timedelta(hours=3))
        n2 = Newsletter.objects.create(name='Newsletter2',
                                       status=Newsletter.STATUS_ONLINE,
                                       published_at=datetime.now() - datetime.timedelta(hours=2))
        n3 = Newsletter.objects.create(name='Newsletter3',
                                       status=Newsletter.STATUS_ONLINE,
                                       published_at=datetime.now() - datetime.timedelta(hours=1))

        self.assertEqual(n2.get_previous(), n1)
        self.assertEqual(n2.get_next(), n3)