from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from courriers.forms import SubscriptionForm
from courriers.models import NewsletterSubscriber


class SubscribeFormTest(TestCase):

    def test_subscription_logged_out(self):
        valid_data = {'receiver': 'adele@ulule.com'}

        form = SubscriptionForm(data=valid_data)

        self.failUnless(form.is_valid())

        subscriber = form.save()

        self.failUnlessEqual(subscriber.receiver, valid_data['receiver'])

        new_subscriber = NewsletterSubscriber.objects.get(email=subscriber.receiver)

        self.assertEqual(new_subscriber.count(), 1)

        # if exists
        form = SubscriptionForm(data=valid_data)

        subscriber = form.save()

        new_subscriber = NewsletterSubscriber.objects.get(email=subscriber.receiver)

        self.assertEqual(new_subscriber.count(), 1)

    def test_subscription_logged_in(self):
        self.client.login(username='adele', password='secret')

        valid_data = {'receiver': 'adele@ulule.com'}

        form = SubscriptionForm(data=valid_data)

        self.failUnless(form.is_valid())

        user = User.objects.get(username='adele')

        subscriber = form.save(user)

        new_subscriber = NewsletterSubscriber.objects.get(email=subscriber.receiver, user=user)

        self.assertEqual(new_subscriber.count(), 1)


class NewslettersViewsTests(TestCase):

    def test_newsletter_list(self):
        response = self.client.get(reverse('newsletter_list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courriers/newsletter_list.html')

    def test_newsletter_detail(self):
        self.client.login(username='adele', password='secret')
        response = self.client.get(reverse('newsletter_detail', kwargs={'pk': 2}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courriers/newsletter_detail.html')

        self.failUnless(isinstance(response.context['form'], SubscriptionForm))

    def test_newsletterraw_detail(self):
        self.client.login(username='adele', password='secret')
        response = self.client.get(reverse('newsletterraw_detail', kwargs={'pk': 2}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courriers/newsletterraw_detail.html')
