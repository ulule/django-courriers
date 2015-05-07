# -*- coding: utf-8 -*-
import mock

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils import timezone as datetime
from django.core import mail

from courriers.forms import SubscriptionForm, UnsubscribeForm
from courriers.models import Newsletter, NewsletterList, NewsletterSubscriber
from courriers.tasks import subscribe, unsubscribe

from django.conf import settings as djsettings

from courriers import settings


class BaseBackendTests(TestCase):
    def setUp(self):
        from courriers.backends import get_backend

        self.backend_klass = get_backend()
        self.backend = self.backend_klass()

        current = datetime.now().strftime('%Y-%m-%d %H:%M')

        self.monthly = NewsletterList.objects.create(name="TestMonthly", slug="testmonthly", languages=['fr'])
        self.weekly = NewsletterList.objects.create(name="TestWeekly", slug="testweekly", languages=['fr'])

        n1 = Newsletter.objects.create(name="3000 projets financés %s" % current,
                                       published_at=datetime.now() - datetime.timedelta(hours=2),
                                       status=Newsletter.STATUS_ONLINE,
                                       newsletter_list=self.monthly)

        n2 = Newsletter.objects.create(name="3000 projets financés %s [monthly][fr]" % current,
                                       published_at=datetime.now() - datetime.timedelta(hours=2),
                                       status=Newsletter.STATUS_ONLINE,
                                       newsletter_list=self.monthly,
                                       languages=['fr'])

        n3 = Newsletter.objects.create(name="3000 projets financés %s [monthly][en-us]" % current,
                                       published_at=datetime.now() - datetime.timedelta(hours=2),
                                       status=Newsletter.STATUS_ONLINE,
                                       newsletter_list=self.weekly,
                                       languages=['en-us'])

        n4 = Newsletter.objects.create(name="3000 projets financés %s [weekly][fr]" % current,
                                       published_at=datetime.now() - datetime.timedelta(hours=2),
                                       status=Newsletter.STATUS_ONLINE,
                                       newsletter_list=self.weekly,
                                       languages=['fr'])

        self.newsletters = [n1, n2, n3, n4]

    def test_registration(self):
        self.backend.register('adele@ulule.com', self.monthly, 'fr')
        self.backend.register('adele@ulule.com', self.weekly, 'fr')

        subscriber = NewsletterSubscriber.objects.filter(email='adele@ulule.com',
                                                         newsletter_list=self.monthly,
                                                         is_unsubscribed=False)
        self.assertEqual(subscriber.count(), 1)

        subscriber2 = NewsletterSubscriber.objects.filter(email='adele@ulule.com',
                                                          newsletter_list=self.weekly,
                                                          is_unsubscribed=False)
        self.assertEqual(subscriber2.count(), 1)

        # Unsubscribe from all
        self.backend.unregister('adele@ulule.com')

        subscriber = NewsletterSubscriber.objects.filter(email='adele@ulule.com',
                                                         is_unsubscribed=True)
        self.assertEqual(subscriber.count(), 2)  # subscriber is unsubscribed from all

        # Subscribe to all
        self.backend.register('adele@ulule.com', self.monthly, 'fr')
        self.backend.register('adele@ulule.com', self.weekly, 'fr')

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

        # Subscribe with capital letters
        self.backend.register('Florent@ulule.com', self.monthly, 'fr')

        self.backend.unregister('florent@ulule.com')

        subscriber = NewsletterSubscriber.objects.filter(email='Florent@ulule.com',
                                                         is_unsubscribed=True)
        self.assertEqual(subscriber.count(), 1)


class SimpleBackendTests(BaseBackendTests):
    def test_registration(self):
        super(SimpleBackendTests, self).test_registration()

        self.backend.register('adele@ulule.com', self.newsletters[0].newsletter_list)

        self.backend.send_mails(self.newsletters[0])
        self.assertEqual(len(mail.outbox), NewsletterSubscriber.objects.subscribed().filter(newsletter_list=self.newsletters[0].newsletter_list).count())
        out = len(mail.outbox)

        self.backend.register('adele@ulule.com', self.newsletters[0].newsletter_list, 'fr')

        self.backend.send_mails(self.newsletters[1])
        self.assertEqual(len(mail.outbox) - out, NewsletterSubscriber.objects.subscribed().filter(newsletter_list=self.newsletters[1].newsletter_list).has_lang('fr').count())
        out = len(mail.outbox)

        self.backend.register('adele@ulule.com', self.newsletters[0].newsletter_list, 'en-us')

        self.backend.send_mails(self.newsletters[2])
        self.assertEqual(len(mail.outbox) - out, NewsletterSubscriber.objects.subscribed().filter(newsletter_list=self.newsletters[2].newsletter_list).has_lang('en-us').count())


class NewslettersViewsTests(TestCase):
    def setUp(self):
        self.monthly = NewsletterList.objects.create(name="TestMonthly", slug="testmonthly")
        self.n1 = Newsletter.objects.create(name='Newsletter1',
                                            newsletter_list=self.monthly,
                                            published_at=datetime.now(),
                                            status=Newsletter.STATUS_DRAFT)

        self.user = User.objects.create_user('adele', 'adele@ulule.com', '$ecret')

    def test_newsletter_list(self):
        response = self.client.get(self.monthly.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courriers/newsletter_list.html')

    def test_newsletter_detail_view(self):
        response = self.client.get(self.n1.get_absolute_url())
        self.assertEqual(response.status_code, 404)

        self.n1.status = Newsletter.STATUS_ONLINE
        self.n1.save()

        response = self.client.get(self.n1.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, 'courriers/newsletter_detail.html')

    def test_newsletter_list_subscribe_view(self):
        response = self.client.get(reverse('newsletter_list_subscribe',
                                   kwargs={'slug': self.monthly.slug}))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('newsletter_list_subscribe',
                                   kwargs={'slug': self.monthly.slug}),
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        self.assertTrue(isinstance(response.context['form'], SubscriptionForm))

    def test_newsletter_list_subscribe_errors(self):
        subscriber = NewsletterSubscriber.objects.create(newsletter_list=self.monthly,
                                                         email='adele@ulule.com',
                                                         lang=djsettings.LANGUAGE_CODE)

        response = self.client.post(reverse('newsletter_list_subscribe',
                                    kwargs={'slug': self.monthly.slug}),
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                                    data={'receiver': subscriber.email})
        self.assertEqual(response.status_code, 200)

        self.assertFalse(response.context['form'].is_valid())
        self.assertTrue('receiver' in response.context['form'].errors)

        subscriber.unsubscribe()

    def test_newsletter_list_unsubscribe_view(self):
        url = reverse('newsletter_list_unsubscribe',
                      kwargs={'slug': 'testmonthly'}) + '?email=adele@ulule.com'

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courriers/newsletter_list_unsubscribe.html')

        self.assertTrue(isinstance(response.context['form'], UnsubscribeForm))

        response = self.client.get(url, {'form': response.context['form']}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_newsletter_list_unsubscribe_complete(self):
        url = reverse('newsletter_list_unsubscribe',
                      kwargs={'slug': 'testmonthly'}) + '?email=adele@ulule.com'

        # GET
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, data={
            'email': 'adele@ulule.com'
        })
        self.assertIn('email', response.context['form'].errors)
        self.assertEqual(response.context['form'].initial['email'], 'adele@ulule.com')
        self.assertEqual(response.status_code, 200)

        # Without email param
        valid_data = {'email': 'adele@ulule.com'}

        NewsletterSubscriber.objects.create(newsletter_list=self.monthly, email='adele@ulule.com')

        response = self.client.post(reverse('newsletter_list_unsubscribe',
                                            kwargs={'slug': 'testmonthly'}),
                                    data=valid_data)

        self.assertRedirects(
            response,
            expected_url=reverse('newsletter_list_unsubscribe_done', args=[self.monthly.slug]),
            status_code=302,
            target_status_code=200
        )

        subscriber = NewsletterSubscriber.objects.get(email='adele@ulule.com')

        self.assertFalse(subscriber.subscribed)

        # With capital letters
        valid_data = {'email': 'Florent@ulule.com'}

        NewsletterSubscriber.objects.create(newsletter_list=self.monthly, email='florent@ulule.com')

        response = self.client.post(reverse('newsletter_list_unsubscribe',
                                            kwargs={'slug': 'testmonthly'}),
                                    data=valid_data)

        self.assertRedirects(
            response,
            expected_url=reverse('newsletter_list_unsubscribe_done', args=[self.monthly.slug]),
            status_code=302,
            target_status_code=200
        )

        subscriber = NewsletterSubscriber.objects.get(email='florent@ulule.com')

        self.assertFalse(subscriber.subscribed)

    def test_newsletter_list_all_unsubscribe_view(self):
        url = reverse('newsletter_list_unsubscribe') + '?email=adele@ulule.com'

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courriers/newsletter_list_unsubscribe.html')

        self.assertTrue(isinstance(response.context['form'], UnsubscribeForm))

        response = self.client.get(url, {'form': response.context['form']}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_newsletter_list_all_unsubscribe_complete(self):
        url = reverse('newsletter_list_unsubscribe') + '?email=adele@ulule.com'

        NewsletterSubscriber.objects.create(newsletter_list=self.monthly, email='adele@ulule.com')

        # GET
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, data={
            'email': 'adele@ulule.com'
        })

        self.assertRedirects(
            response,
            expected_url=reverse('newsletter_list_unsubscribe_done'),
            status_code=302,
            target_status_code=200
        )

        subscriber = NewsletterSubscriber.objects.get(email='adele@ulule.com')
        self.assertFalse(subscriber.subscribed)

    def test_newsletter_raw_detail_view(self):
        response = self.client.get(reverse('newsletter_raw_detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courriers/newsletter_raw_detail.html')


class SubscribeFormTest(TestCase):
    def setUp(self):
        from courriers.backends import get_backend

        self.backend_klass = get_backend()
        self.backend = self.backend_klass()

        self.monthly = NewsletterList.objects.create(name="TestMonthly", slug="testmonthly")

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

    def test_subscribe_task(self):
        subscribe.apply_async(kwargs={'email': 'adele@ulule.com',
                                      'newsletter_list_id': self.monthly.pk,
                                      'lang': 'fr'})

        new_subscriber = NewsletterSubscriber.objects.filter(email='adele@ulule.com', is_unsubscribed=False)
        self.assertEqual(new_subscriber.count(), 1)


class NewDatetime(datetime.datetime):
    @classmethod
    def now(cls):
        return cls(2014, 4, 9, 9, 56, 2, 342715)


@mock.patch.object(settings, 'BACKEND_CLASS', 'courriers.backends.simple.SimpleBackend')
class UnsubscribeFormTest(TestCase):
    def setUp(self):
        from courriers.backends import get_backend
        datetime.datetime = NewDatetime

        self.backend_klass = get_backend()
        self.backend = self.backend_klass()

        self.monthly = NewsletterList.objects.create(name="TestMonthly", slug="testmonthly")
        self.weekly = NewsletterList.objects.create(name="TestWeekly", slug="testweekly")
        self.daily = NewsletterList.objects.create(name="TestDaily", slug="testdaily")

    def test_unsubscription(self):
        self.backend.unregister('adele@ulule.com', self.monthly, 'fr')

        self.backend.register('adele@ulule.com', self.monthly, 'fr')
        self.backend.register('adele@ulule.com', self.weekly, 'fr')
        self.backend.register('adele@ulule.com', self.daily, 'fr')

        # Unsubscribe from monthly
        valid_data = {'email': 'adele@ulule.com', 'from_all': False}

        form = UnsubscribeForm(data=valid_data, initial={'email': 'adele@ulule.com'}, **{'newsletter_list': self.monthly})

        self.assertTrue(form.is_valid())

        form.save()

        old_subscriber = NewsletterSubscriber.objects.get(email=valid_data['email'],
                                                          newsletter_list=self.monthly)
        old_subscriber2 = NewsletterSubscriber.objects.get(email=valid_data['email'],
                                                           newsletter_list=self.weekly)

        self.assertEqual(old_subscriber.is_unsubscribed, True)
        self.assertEqual(old_subscriber.unsubscribed_at, datetime.now())
        self.assertEqual(old_subscriber2.is_unsubscribed, False)

        # Unsubscribe from all
        valid_data = {'email': 'adele@ulule.com', 'from_all': True}

        form = UnsubscribeForm(data=valid_data, newsletter_list=self.weekly)

        self.assertTrue(form.is_valid())

        form.save()

        old_subscriber = NewsletterSubscriber.objects.filter(email=valid_data['email'],
                                                             newsletter_list=self.weekly)
        old_subscriber2 = NewsletterSubscriber.objects.filter(email=valid_data['email'],
                                                              newsletter_list=self.daily)

        self.assertEqual(old_subscriber.get().is_unsubscribed, True)
        self.assertEqual(old_subscriber2.get().is_unsubscribed, True)
        self.assertEqual(old_subscriber2.get().unsubscribed_at, datetime.now())

        form2 = UnsubscribeForm(data=valid_data, newsletter_list=self.weekly)

        is_valid = form2.is_valid()

        self.assertEqual(is_valid, False)

    def test_unsubscription_logged_in(self):
        user = User.objects.create_user('thoas', 'florent@ulule.com', 'secret')

        self.backend.register('florent@ulule.com', self.monthly, 'fr', user=user)
        new_subscriber = NewsletterSubscriber.objects.filter(email='florent@ulule.com', user=user)
        self.assertEqual(new_subscriber.count(), 1)

        valid_data = {'email': 'florent@ulule.com', 'from_all': False}

        form = UnsubscribeForm(data=valid_data, initial={'email': 'florent@ulule.com'}, **{'newsletter_list': self.monthly})

        self.assertTrue(form.is_valid())

        form.save(user)  # Equivalent for saving with user logged in

        self.backend.unregister('florent@ulule.com')

    def test_unsubscribe_task(self):
        NewsletterSubscriber.objects.create(newsletter_list=self.monthly, email='adele@ulule.com')

        unsubscribe.apply_async(kwargs={'email': 'adele@ulule.com',
                                        'newsletter_list_id': self.monthly.pk})

        new_subscriber = NewsletterSubscriber.objects.filter(email='adele@ulule.com',
                                                             newsletter_list=self.monthly,
                                                             is_unsubscribed=True)
        self.assertEqual(new_subscriber.count(), 1)


if hasattr(settings, 'COURRIERS_MAILCHIMP_API_KEY'):
    @mock.patch.object(settings, 'BACKEND_CLASS', 'courriers.backends.mailchimp.MailchimpBackend')
    class SubscribeMailchimpFormTest(SubscribeFormTest):
        pass

    @mock.patch.object(settings, 'BACKEND_CLASS', 'courriers.backends.mailchimp.MailchimpBackend')
    class UnsubscribeMailchimpFormTest(UnsubscribeFormTest):
        pass

    @mock.patch.object(settings, 'BACKEND_CLASS', 'courriers.backends.mailchimp.MailchimpBackend')
    class MailchimpBackendTests(BaseBackendTests):
        def test_registration(self):
            super(MailchimpBackendTests, self).test_registration()

            for newsletter in self.newsletters:
                self.backend.send_mails(newsletter)


if hasattr(settings, 'COURRIERS_MAILJET_API_KEY') and hasattr(settings, 'COURRIERS_MAILJET_API_SECRET_KEY'):
    @mock.patch.object(settings, 'BACKEND_CLASS', 'courriers.backends.mailjet.MailjetBackend')
    class SubscribeMailjetFormTest(SubscribeFormTest):
        pass

    @mock.patch.object(settings, 'BACKEND_CLASS', 'courriers.backends.mailjet.MailjetBackend')
    class UnsubscribeMailjetFormTest(UnsubscribeFormTest):
        pass

    @mock.patch.object(settings, 'BACKEND_CLASS', 'courriers.backends.mailjet.MailjetBackend')
    class MailjetBackendTests(BaseBackendTests):
        def test_registration(self):
            super(MailjetBackendTests, self).test_registration()

            for newsletter in self.newsletters:
                self.backend.send_mails(newsletter)


class NewsletterModelsTest(TestCase):
    def test_navigation(self):
        monthly = NewsletterList.objects.create(name="TestMonthly", slug="testmonthly")

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
