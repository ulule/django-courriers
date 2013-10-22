from django.test import TestCase

from django.core.urlresolvers import reverse


class NewslettersViewsTests(TestCase):

	def test_newsletter_detail(self):
		response = self.client.get(reverse('newsletter_detail', kwargs={'pk': 2}))

		self.assertEqual(response.status_code, 200)