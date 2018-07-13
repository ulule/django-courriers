# -*- coding: utf-8 -*-
import mock

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone as datetime
from django.core import mail

from courriers.forms import SubscriptionForm, UnsubscribeForm
from courriers.models import Newsletter, NewsletterList, NewsletterSegment
from courriers import settings
from courriers.tasks import subscribe, unsubscribe

from .models import NewsletterSubscriber

User = get_user_model()


class BaseBackendTests(TestCase):
    def setUp(self):
        from courriers.backends import get_backend

        self.backend_klass = get_backend()
        self.backend = self.backend_klass()

        current = datetime.now().strftime("%Y-%m-%d %H:%M")

        self.monthly = NewsletterList.objects.create(
            name="TestMonthly", slug="testmonthly", list_id=1
        )
        self.weekly = NewsletterList.objects.create(
            name="TestWeekly", slug="testweekly", list_id=2
        )

        self.segment_monthly = NewsletterSegment.objects.create(
            name="monthly", segment_id=3, newsletter_list=self.monthly
        )
        self.segment_weekly = NewsletterSegment.objects.create(
            name="weekly", segment_id=3, newsletter_list=self.weekly
        )

        self.segment_monthly_fr = NewsletterSegment.objects.create(
            name="monthly fr", segment_id=3, newsletter_list=self.monthly, lang="fr"
        )
        self.segment_weekly_fr = NewsletterSegment.objects.create(
            name="weekly fr", segment_id=4, newsletter_list=self.weekly, lang="fr"
        )

        self.segment_monthly_en = NewsletterSegment.objects.create(
            name="monthly en", segment_id=4, newsletter_list=self.monthly, lang="en-us"
        )

        self.nl_monthly = Newsletter.objects.create(
            name="3000 projets financés %s" % current,
            published_at=datetime.now() - datetime.timedelta(hours=2),
            status=Newsletter.STATUS_ONLINE,
            newsletter_list=self.monthly,
            newsletter_segment=self.segment_monthly,
        )

        self.nl_monthly_fr = Newsletter.objects.create(
            name="3000 projets financés %s [monthly][fr]" % current,
            published_at=datetime.now() - datetime.timedelta(hours=2),
            status=Newsletter.STATUS_ONLINE,
            newsletter_list=self.monthly,
            newsletter_segment=self.segment_monthly_fr,
        )
        self.nl_monthly_en = Newsletter.objects.create(
            name="3000 projects %s" % current,
            published_at=datetime.now() - datetime.timedelta(hours=2),
            status=Newsletter.STATUS_ONLINE,
            newsletter_list=self.monthly,
            newsletter_segment=self.segment_monthly_en,
        )

        self.nl_weekly = Newsletter.objects.create(
            name="3000 projets financés %s [monthly][en-us]" % current,
            published_at=datetime.now() - datetime.timedelta(hours=2),
            status=Newsletter.STATUS_ONLINE,
            newsletter_list=self.weekly,
            newsletter_segment=self.segment_weekly,
        )

        self.nl_weekly_fr = Newsletter.objects.create(
            name="3000 projets financés %s [weekly][fr]" % current,
            published_at=datetime.now() - datetime.timedelta(hours=2),
            status=Newsletter.STATUS_ONLINE,
            newsletter_list=self.weekly,
            newsletter_segment=self.segment_weekly_fr,
        )

        self.user = User.objects.create_user("adele", "adele@ulule.com", "$ecret")

    def test_registration(self):
        self.backend.register("adele@ulule.com", self.monthly, "fr")
        self.backend.register("adele@ulule.com", self.weekly, "fr")

        subscriber = NewsletterSubscriber.objects.filter(
            email="adele@ulule.com", newsletter_list=self.monthly, is_unsubscribed=False
        )
        self.assertEqual(subscriber.count(), 1)

        subscriber2 = NewsletterSubscriber.objects.filter(
            email="adele@ulule.com", newsletter_list=self.weekly, is_unsubscribed=False
        )
        self.assertEqual(subscriber2.count(), 1)

        # Unsubscribe from all
        self.backend.unregister("adele@ulule.com")

        subscriber = NewsletterSubscriber.objects.filter(
            email="adele@ulule.com", is_unsubscribed=True
        )
        self.assertEqual(subscriber.count(), 2)  # subscriber is unsubscribed from all

        # Subscribe to all
        self.backend.register("adele@ulule.com", self.monthly, "fr")
        self.backend.register("adele@ulule.com", self.weekly, "fr")

        subscriber = NewsletterSubscriber.objects.get(
            email="adele@ulule.com", newsletter_list=self.monthly, is_unsubscribed=False
        )

        # Unsubscribe from monthly
        self.backend.unregister(subscriber.email, self.monthly)

        unsubscriber = NewsletterSubscriber.objects.filter(
            email="adele@ulule.com", newsletter_list=self.monthly, is_unsubscribed=True
        )
        self.assertEqual(unsubscriber.count(), 1)

        unsubscriber = NewsletterSubscriber.objects.filter(
            email="adele@ulule.com", newsletter_list=self.weekly, is_unsubscribed=False
        )
        self.assertEqual(unsubscriber.count(), 1)


class SimpleBackendTests(BaseBackendTests):
    def test_registration(self):
        super(SimpleBackendTests, self).test_registration()

        self.backend.register("adele@ulule.com", self.nl_monthly.newsletter_list)

        self.backend.send_mails(
            self.nl_monthly,
            subscribers=NewsletterSubscriber.objects.filter(
                newsletter_list=self.monthly
            ),
        )

        self.assertEqual(len(mail.outbox), 1)
        out = len(mail.outbox)

        self.backend.register(
            "adele@ulule.com", self.nl_monthly_fr.newsletter_list, "fr"
        )

        self.backend.send_mails(
            self.nl_monthly_fr,
            subscribers=NewsletterSubscriber.objects.filter(
                newsletter_list=self.monthly
            ),
        )

        self.assertEqual(len(mail.outbox) - out, 1)
        out = len(mail.outbox)

        self.backend.register("adele@ulule.com", self.monthly, "en-us")

        self.backend.send_mails(
            self.nl_monthly_en,
            subscribers=NewsletterSubscriber.objects.filter(
                newsletter_list=self.monthly
            ),
        )

        self.assertEqual(len(mail.outbox) - out, 1)


class NewslettersViewsTests(TestCase):
    def setUp(self):
        self.monthly = NewsletterList.objects.create(
            name="TestMonthly", slug="testmonthly"
        )
        self.segment_monthly = NewsletterSegment.objects.create(
            name="monthly fr", segment_id=3, newsletter_list=self.monthly, lang="fr"
        )
        self.n1 = Newsletter.objects.create(
            name="Newsletter1",
            newsletter_list=self.monthly,
            newsletter_segment=self.segment_monthly,
            published_at=datetime.now(),
            status=Newsletter.STATUS_DRAFT,
        )

        self.user = User.objects.create_user("adele", "adele@ulule.com", "$ecret")

    def test_newsletter_list(self):
        response = self.client.get(self.monthly.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "courriers/newsletter_list.html")

    def test_newsletter_detail_view(self):
        response = self.client.get(self.n1.get_absolute_url())
        self.assertEqual(response.status_code, 404)

        self.n1.status = Newsletter.STATUS_ONLINE
        self.n1.save()

        response = self.client.get(self.n1.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, "courriers/newsletter_detail.html")

    def test_newsletter_list_subscribe_view(self):
        response = self.client.get(
            reverse("newsletter_list_subscribe", kwargs={"slug": self.monthly.slug})
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            reverse("newsletter_list_subscribe", kwargs={"slug": self.monthly.slug}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)

        self.assertTrue(isinstance(response.context["form"], SubscriptionForm))

    def test_newsletter_list_unsubscribe_view(self):
        url = (
            reverse("newsletter_list_unsubscribe", kwargs={"slug": "testmonthly"})
            + "?email=adele@ulule.com"
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "courriers/newsletter_list_unsubscribe.html")

        self.assertTrue(isinstance(response.context["form"], UnsubscribeForm))

        response = self.client.get(
            url,
            {"form": response.context["form"]},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)

    def test_newsletter_list_unsubscribe_complete(self):
        # Without email param
        valid_data = {"email": "adele@ulule.com"}

        NewsletterSubscriber.objects.create(
            newsletter_list=self.monthly, email="adele@ulule.com", user=self.user
        )

        response = self.client.post(
            reverse("newsletter_list_unsubscribe", kwargs={"slug": "testmonthly"}),
            data=valid_data,
        )

        self.assertRedirects(
            response,
            expected_url=reverse(
                "newsletter_list_unsubscribe_done", args=[self.monthly.slug]
            ),
            status_code=302,
            target_status_code=200,
        )

        subscriber = NewsletterSubscriber.objects.get(email="adele@ulule.com")

        self.assertFalse(subscriber.subscribed)

    def test_newsletter_list_all_unsubscribe_view(self):
        url = reverse("newsletter_list_unsubscribe") + "?email=adele@ulule.com"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "courriers/newsletter_list_unsubscribe.html")

        self.assertTrue(isinstance(response.context["form"], UnsubscribeForm))

        response = self.client.get(
            url,
            {"form": response.context["form"]},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)

    def test_newsletter_list_all_unsubscribe_complete(self):
        url = reverse("newsletter_list_unsubscribe") + "?email=adele@ulule.com"
        NewsletterSubscriber.objects.create(
            newsletter_list=self.monthly, email="adele@ulule.com", user=self.user
        )

        # GET
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, data={"email": "adele@ulule.com"})

        self.assertRedirects(
            response,
            expected_url=reverse("newsletter_list_unsubscribe_done"),
            status_code=302,
            target_status_code=200,
        )

        subscriber = NewsletterSubscriber.objects.get(email="adele@ulule.com")
        self.assertFalse(subscriber.subscribed)

    def test_newsletter_raw_detail_view(self):
        response = self.client.get(reverse("newsletter_raw_detail", kwargs={"pk": 1}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "courriers/newsletter_raw_detail.html")


class SubscribeFormTest(TestCase):
    def setUp(self):
        from courriers.backends import get_backend

        self.backend_klass = get_backend()
        self.backend = self.backend_klass()

        self.monthly = NewsletterList.objects.create(
            name="TestMonthly", slug="testmonthly"
        )
        self.segment_monthly = NewsletterSegment.objects.create(
            name="monthly fr", segment_id=3, newsletter_list=self.monthly, lang="fr"
        )

    def test_subscription_logged_in(self):
        self.client.login(username="thoas", password="secret")

        valid_data = {"receiver": "florent@ulule.com"}

        form = SubscriptionForm(data=valid_data, **{"newsletter_list": self.monthly})

        self.assertTrue(form.is_valid())

        user = User.objects.create(username="thoas", email="florent@ulule.com")
        form.save(user)

        new_subscriber = NewsletterSubscriber.objects.filter(
            email=valid_data["receiver"], user=user
        )

        self.assertEqual(new_subscriber.count(), 1)

        self.backend.unregister("florent@ulule.com")

    def test_subscribe_task(self):
        user = User.objects.create(username="adele-ulule", email="adele@ulule.com")
        subscribe.apply_async(
            kwargs={
                "email": "adele@ulule.com",
                "newsletter_list_id": self.monthly.pk,
                "lang": "fr",
            }
        )

        new_subscriber = NewsletterSubscriber.objects.filter(
            email="adele@ulule.com", is_unsubscribed=False
        )
        self.assertEqual(new_subscriber.count(), 1)


class NewDatetime(datetime.datetime):
    @classmethod
    def now(cls):
        return cls(2014, 4, 9, 9, 56, 2, 342715)


@mock.patch.object(settings, "BACKEND_CLASS", "courriers.backends.simple.SimpleBackend")
class UnsubscribeFormTest(TestCase):
    def setUp(self):
        from courriers.backends import get_backend

        datetime.datetime = NewDatetime

        self.backend_klass = get_backend()
        self.backend = self.backend_klass()

        self.monthly = NewsletterList.objects.create(
            name="TestMonthly", slug="testmonthly"
        )
        self.weekly = NewsletterList.objects.create(
            name="TestWeekly", slug="testweekly"
        )
        self.daily = NewsletterList.objects.create(name="TestDaily", slug="testdaily")

        self.user = User.objects.create_user("adele", "adele@ulule.com", "$ecret")

    def test_unsubscription(self):
        self.backend.unregister("adele@ulule.com", self.monthly, lang="fr")

        self.backend.register("adele@ulule.com", self.monthly, lang="fr")
        self.backend.register("adele@ulule.com", self.weekly, lang="fr")
        self.backend.register("adele@ulule.com", self.daily, lang="fr")

        # Unsubscribe from monthly
        valid_data = {"email": "adele@ulule.com", "from_all": False}

        form = UnsubscribeForm(
            data=valid_data,
            initial={"email": "adele@ulule.com"},
            **{"newsletter_list": self.monthly}
        )

        self.assertTrue(form.is_valid())

        form.save()

        old_subscriber = NewsletterSubscriber.objects.get(
            email=valid_data["email"], newsletter_list=self.monthly
        )
        old_subscriber2 = NewsletterSubscriber.objects.get(
            email=valid_data["email"], newsletter_list=self.weekly
        )

        self.assertEqual(old_subscriber.is_unsubscribed, True)
        self.assertEqual(old_subscriber.unsubscribed_at, datetime.now())
        self.assertEqual(old_subscriber2.is_unsubscribed, False)

        # Unsubscribe from all
        valid_data = {"email": "adele@ulule.com", "from_all": True}

        form = UnsubscribeForm(data=valid_data, newsletter_list=self.weekly)

        self.assertTrue(form.is_valid())

        form.save()

        old_subscriber = NewsletterSubscriber.objects.filter(
            email=valid_data["email"], newsletter_list=self.weekly
        )
        old_subscriber2 = NewsletterSubscriber.objects.filter(
            email=valid_data["email"], newsletter_list=self.daily
        )

        self.assertEqual(old_subscriber.get().is_unsubscribed, True)
        self.assertEqual(old_subscriber2.get().is_unsubscribed, True)
        self.assertEqual(old_subscriber2.get().unsubscribed_at, datetime.now())

    def test_unsubscription_logged_in(self):
        user = User.objects.create_user("thoas", "florent@ulule.com", "secret")

        self.backend.register("florent@ulule.com", self.monthly, "fr", user=user)
        new_subscriber = NewsletterSubscriber.objects.filter(
            email="florent@ulule.com", user=user
        )
        self.assertEqual(new_subscriber.count(), 1)

        valid_data = {"email": "florent@ulule.com", "from_all": False}

        form = UnsubscribeForm(
            data=valid_data,
            initial={"email": "florent@ulule.com"},
            **{"newsletter_list": self.monthly}
        )

        self.assertTrue(form.is_valid())

        form.save(user)  # Equivalent for saving with user logged in

        self.backend.unregister("florent@ulule.com")

    def test_unsubscribe_task(self):
        NewsletterSubscriber.objects.create(
            newsletter_list=self.monthly, email="adele@ulule.com", user=self.user
        )

        unsubscribe.apply_async(
            kwargs={"email": "adele@ulule.com", "newsletter_list_id": self.monthly.pk}
        )

        new_subscriber = NewsletterSubscriber.objects.filter(
            email="adele@ulule.com", newsletter_list=self.monthly, is_unsubscribed=True
        )
        self.assertEqual(new_subscriber.count(), 1)


if hasattr(settings, "COURRIERS_MAILJET_API_KEY") and hasattr(
    settings, "COURRIERS_MAILJET_API_SECRET_KEY"
):

    @mock.patch.object(
        settings, "BACKEND_CLASS", "courriers.backends.mailjet.MailjetBackend"
    )
    class SubscribeMailjetFormTest(SubscribeFormTest):
        pass

    @mock.patch.object(
        settings, "BACKEND_CLASS", "courriers.backends.mailjet.MailjetBackend"
    )
    class UnsubscribeMailjetFormTest(UnsubscribeFormTest):
        pass

    @mock.patch.object(
        settings, "BACKEND_CLASS", "courriers.backends.mailjet.MailjetBackend"
    )
    class MailjetBackendTests(BaseBackendTests):
        def test_registration(self):
            super(MailjetBackendTests, self).test_registration()

            for newsletter in self.newsletters:
                self.backend.send_mails(newsletter)


class NewsletterModelsTest(TestCase):
    def test_navigation(self):
        monthly = NewsletterList.objects.create(name="TestMonthly", slug="testmonthly")
        segment_monthly = NewsletterSegment.objects.create(
            name="monthly fr", segment_id=3, newsletter_list=monthly, lang="fr"
        )

        Newsletter.objects.create(
            name="Newsletter4",
            status=Newsletter.STATUS_DRAFT,
            published_at=datetime.now() - datetime.timedelta(hours=4),
            newsletter_list=monthly,
            newsletter_segment=segment_monthly,
        )
        n1 = Newsletter.objects.create(
            name="Newsletter1",
            status=Newsletter.STATUS_ONLINE,
            published_at=datetime.now() - datetime.timedelta(hours=3),
            newsletter_list=monthly,
            newsletter_segment=segment_monthly,
        )
        n2 = Newsletter.objects.create(
            name="Newsletter2",
            status=Newsletter.STATUS_ONLINE,
            published_at=datetime.now() - datetime.timedelta(hours=2),
            newsletter_list=monthly,
            newsletter_segment=segment_monthly,
        )
        n3 = Newsletter.objects.create(
            name="Newsletter3",
            status=Newsletter.STATUS_ONLINE,
            published_at=datetime.now() - datetime.timedelta(hours=1),
            newsletter_list=monthly,
            newsletter_segment=segment_monthly,
        )

        self.assertEqual(n2.get_previous(), n1)
        self.assertEqual(n2.get_next(), n3)
        self.assertEqual(n1.get_previous(), None)
