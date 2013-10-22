from django.test import TestCase
from django.contrib.auth import User

from ..forms import SubscribeForm
from ..models import NewsletterSubscriber


class SubscribeFormTests(TestCase):

	def test_subscription_logged_out(self):
		valid_data = {'receiver': 'adele@ulule.com'}

		form = SubscribeForm(data=valid_data)

		self.failUnless(form.is_valid())

		subscriber = form.save()

		new_subscriber = NewsletterSubscriber.objects.get(email=subscriber.receiver)

		self.assertEqual(new_subscriber.count(), 1)

	def test_subscription_logged_in(self):
		self.client.login(username='adele', password='secret')

		valid_data = {'receiver': 'adele@ulule.com'}

		form = SubscribeForm(data=valid_data)

		self.failUnless(form.is_valid())

		user = User.objects.get(username='adele')

		subscriber = form.save(user)

		new_subscriber = NewsletterSubscriber.objects.get(email=subscriber.receiver, user=user)

		self.assertEqual(new_subscriber.count(), 1)