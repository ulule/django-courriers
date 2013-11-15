# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test.utils import override_settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils import timezone as datetime
from django.core import mail

from courriers.forms import SubscriptionForm, NewsletterListUnsubscribeForm
from courriers.models import Newsletter, NewsletterList, NewsletterSubscriber

from django.conf import settings


class BaseBackendTests(TestCase):
    def setUp(self):
        from courriers import settings
        reload(settings)

        from courriers.backends import get_backend

        self.backend_klass = get_backend()
        self.backend = self.backend_klass()

        self.monthly = NewsletterList.objects.create(name="Monthly", slug="monthly")
        self.weekly = NewsletterList.objects.create(name="Weekly", slug="weekly")

        n1 = Newsletter.objects.create(name="3000 projets finances",
                                       published_at=datetime.now() - datetime.timedelta(hours=2),
                                       status=Newsletter.STATUS_ONLINE,
                                       newsletter_list=self.monthly)

        n2 = Newsletter.objects.create(name="3000 projets finances [FR]",
                                       published_at=datetime.now() - datetime.timedelta(hours=2),
                                       status=Newsletter.STATUS_ONLINE,
                                       newsletter_list=self.monthly,
                                       languages=['FR'])

        n3 = Newsletter.objects.create(name="3000 projets finances [en-us]",
                                       published_at=datetime.now() - datetime.timedelta(hours=2),
                                       status=Newsletter.STATUS_ONLINE,
                                       newsletter_list=self.weekly,
                                       languages=['en-us'])

        self.newsletters = [n1, n2, n3]

    def test_registration(self):
        # Subscribe to all
        self.backend.register('adele@ulule.com', self.monthly, 'FR')
        self.backend.register('adele@ulule.com', self.weekly, 'FR')

        subscriber = NewsletterSubscriber.objects.filter(email='adele@ulule.com',
                                                         newsletter_list=self.monthly,
                                                         is_unsubscribed=False)
        self.assertEqual(subscriber.count(), 1)

        subscriber2 = NewsletterSubscriber.objects.filter(email='adele@ulule.com',
                                                          newsletter_list=self.weekly,
                                                          is_unsubscribed=False)
        self.assertEqual(subscriber2.count(), 1)

        # Unsubscribe from all
        subscriber = NewsletterSubscriber.objects.filter(email='adele@ulule.com')
        for s in subscriber:
            self.backend.unregister(s.email)

        subscriber = NewsletterSubscriber.objects.filter(email='adele@ulule.com',
                                                         is_unsubscribed=True)
        self.assertEqual(subscriber.count(), 2)  # subscriber is unsubscribed from all

        # Subscribe to all
        self.backend.register('adele@ulule.com', self.monthly, 'FR')
        self.backend.register('adele@ulule.com', self.weekly, 'FR')

        subscriber = NewsletterSubscriber.objects.get(email='adele@ulule.com',
                                                      newsletter_list=self.monthly,
                                                      is_unsubscribed=False)

        # Unsubscribe from monthly
        self.backend.unregister(subscriber.email, self.monthly)

        unsubscriber = NewsletterSubscriber.objects.filter(email='adele@ulule.com',
                                                           newsletter_list=self.monthly,
                                                           is_unsubscribed=True)
        self.assertEqual(unsubscriber.count(), 1)

        unsubscriber = NewsletterSubscriber.objects.filter(email='adele@ulule.com',
                                                           newsletter_list=self.weekly,
                                                           is_unsubscribed=False)
        self.assertEqual(unsubscriber.count(), 1)

        unsubscriber = NewsletterSubscriber.objects.filter(email='adele@ulule.com',
                                                           newsletter_list=self.weekly,
                                                           is_unsubscribed=True)
        self.assertEqual(unsubscriber.count(), 0)

        self.backend.unregister('florent@ulule.com')  # Subscriber does not exist


class SimpleBackendTests(BaseBackendTests):
    def test_registration(self):
        super(SimpleBackendTests, self).test_registration()

        self.backend.register('adele@ulule.com', self.newsletters[0])

        self.backend.send_mails(self.newsletters[0])
        self.assertEqual(len(mail.outbox), NewsletterSubscriber.objects.subscribed().filter(newsletter_list=self.newsletters[0].newsletter_list).count())
        out = len(mail.outbox)

        self.backend.register('adele@ulule.com', self.newsletters[0], 'FR')

        self.backend.send_mails(self.newsletters[1])
        self.assertEqual(len(mail.outbox) - out, NewsletterSubscriber.objects.subscribed().filter(newsletter_list=self.newsletters[1].newsletter_list).has_lang('FR').count())
        out = len(mail.outbox)

        self.backend.register('adele@ulule.com', self.newsletters[0], 'en-us')

        self.backend.send_mails(self.newsletters[2])
        self.assertEqual(len(mail.outbox) - out, NewsletterSubscriber.objects.subscribed().filter(newsletter_list=self.newsletters[2].newsletter_list).has_lang('en-us').count())


class NewslettersViewsTests(TestCase):
    def setUp(self):
        self.monthly = NewsletterList.objects.create(name="Monthly", slug="monthly")
        Newsletter.objects.create(name='Newsletter1', newsletter_list=self.monthly, published_at=datetime.now())

    def test_newsletter_list(self):
        response = self.client.get(self.monthly.get_absolute_url())

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

        self.monthly = NewsletterList.objects.create(name="Monthly", slug="monthly")

    def test_subscription_logged_out(self):
        valid_data = {'receiver': 'adele@ulule.com'}

        form = SubscriptionForm(data=valid_data, **{'newsletter_list': self.monthly})

        self.assertTrue(form.is_valid())

        form.save()

        new_subscriber = NewsletterSubscriber.objects.filter(email=valid_data['receiver'])

        self.assertEqual(new_subscriber.count(), 1)
        self.assertNotEqual(new_subscriber.get().lang, None)

        # Test duplicate
        form2 = SubscriptionForm(data=valid_data, **{'newsletter_list': self.monthly})

        is_valid = form2.is_valid()

        self.assertEqual(is_valid, False)

        self.backend.unregister('adele@ulule.com')

    def test_subscription_logged_in(self):
        self.client.login(username='thoas', password='secret')

        valid_data = {'receiver': 'florent@ulule.com'}

        form = SubscriptionForm(data=valid_data, **{'newsletter_list': self.monthly})

        self.assertTrue(form.is_valid())

        user = User.objects.create(username='thoas')

        form.save(user)

        new_subscriber = NewsletterSubscriber.objects.filter(email=valid_data['receiver'], user=user)

        self.assertEqual(new_subscriber.count(), 1)
        self.assertNotEqual(new_subscriber.get().lang, None)

        self.backend.unregister('florent@ulule.com')


@override_settings(COURRIERS_BACKEND_CLASS='courriers.backends.simple.SimpleBackend')
class UnsubscribeFormTest(TestCase):
    def setUp(self):
        from courriers.backends import get_backend

        self.backend_klass = get_backend()
        self.backend = self.backend_klass()

        self.monthly = NewsletterList.objects.create(name="Monthly", slug="monthly")
        self.weekly = NewsletterList.objects.create(name="Weekly", slug="weekly")
        self.daily = NewsletterList.objects.create(name="Daily", slug="daily")

    def test_unsubscription(self):
        self.backend.register('adele@ulule.com', self.monthly, 'FR')
        self.backend.register('adele@ulule.com', self.weekly, 'FR')
        self.backend.register('adele@ulule.com', self.daily, 'FR')

        # Unsubscribe from monthly
        valid_data = {'email': 'adele@ulule.com', 'from_all': False}

        form = NewsletterListUnsubscribeForm(data=valid_data, **{'newsletter_list': self.monthly})

        self.assertTrue(form.is_valid())

        form.save()

        old_subscriber = NewsletterSubscriber.objects.get(email=valid_data['email'],
                                                          newsletter_list=self.monthly)
        old_subscriber2 = NewsletterSubscriber.objects.get(email=valid_data['email'],
                                                           newsletter_list=self.weekly)

        self.assertEqual(old_subscriber.is_unsubscribed, True)
        self.assertEqual(old_subscriber2.is_unsubscribed, False)

        # Unsubscribe from all
        valid_data = {'email': 'adele@ulule.com', 'from_all': True}

        form = NewsletterListUnsubscribeForm(data=valid_data, newsletter_list=self.weekly)

        self.assertTrue(form.is_valid())

        form.save()

        old_subscriber = NewsletterSubscriber.objects.filter(email=valid_data['email'],
                                                             newsletter_list=self.weekly)
        old_subscriber2 = NewsletterSubscriber.objects.filter(email=valid_data['email'],
                                                              newsletter_list=self.daily)

        self.assertEqual(old_subscriber.get().is_unsubscribed, True)
        self.assertEqual(old_subscriber2.get().is_unsubscribed, True)

        form2 = NewsletterListUnsubscribeForm(data=valid_data, newsletter_list=self.weekly)

        is_valid = form2.is_valid()

        self.assertEqual(is_valid, False)


if hasattr(settings, 'COURRIERS_MAILCHIMP_API_KEY'):
    @override_settings(COURRIERS_BACKEND_CLASS='courriers.backends.mailchimp.MailchimpBackend')
    class SubscribeMailchimpFormTest(SubscribeFormTest):
        pass

    @override_settings(COURRIERS_BACKEND_CLASS='courriers.backends.mailchimp.MailchimpBackend')
    class MailchimpBackendTests(BaseBackendTests):
        def test_registration(self):
            super(MailchimpBackendTests, self).test_registration()

            for newsletter in self.newsletters:
                self.backend.send_mails(newsletter)


class NewsletterModelsTest(TestCase):
    def test_navigation(self):
        monthly = NewsletterList.objects.create(name="Monthly", slug="monthly")

        Newsletter.objects.create(name='Newsletter4',
                                  status=Newsletter.STATUS_DRAFT,
                                  published_at=datetime.now() - datetime.timedelta(hours=4),
                                  newsletter_list=monthly)
        n1 = Newsletter.objects.create(name='Newsletter1',
                                       status=Newsletter.STATUS_ONLINE,
                                       published_at=datetime.now() - datetime.timedelta(hours=3),
                                       newsletter_list=monthly)
        n2 = Newsletter.objects.create(name='Newsletter2',
                                       status=Newsletter.STATUS_ONLINE,
                                       published_at=datetime.now() - datetime.timedelta(hours=2),
                                       newsletter_list=monthly)
        n3 = Newsletter.objects.create(name='Newsletter3',
                                       status=Newsletter.STATUS_ONLINE,
                                       published_at=datetime.now() - datetime.timedelta(hours=1),
                                       newsletter_list=monthly)

        self.assertEqual(n2.get_previous(), n1)
        self.assertEqual(n2.get_next(), n3)
        self.assertEqual(n1.get_previous(), None)