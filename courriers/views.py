# -*- coding: utf-8 -*-
from django.views.generic import View, ListView, DetailView, FormView
from django.views.generic.detail import SingleObjectMixin

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.contrib import messages

from .models import Newsletter
from .forms import SubscriptionForm, UnsubscriptionForm


class NewsletterListView(ListView):
    model = Newsletter
    context_object_name = 'newsletters'

    def get_queryset(self):
        return self.model.objects.all().status_online().order_by('published_at')


class NewsletterDisplayView(DetailView):
    model = Newsletter
    context_object_name = 'newsletter'
    template_name = 'courriers/newsletter_detail.html'

    def get_context_data(self, **kwargs):
        context = super(NewsletterDisplayView, self).get_context_data(**kwargs)

        context['previous_object'] = self.model.objects.get_previous(self.object.published_at)
        context['next_object'] = self.model.objects.get_next(self.object.published_at)

        context['form'] = SubscriptionForm(user=self.request.user)

        return context


class NewsletterFormView(FormView, SingleObjectMixin):
    template_name = 'courriers/newsletter_detail.html'
    form_class = SubscriptionForm
    model = Newsletter
    context_object_name = 'newsletter'

    def get_context_data(self, **kwargs):
        self.object = self.get_object()
        context = super(NewsletterFormView, self).get_context_data(**kwargs)
        context.update(SingleObjectMixin.get_context_data(self, **kwargs))
        return context

    def form_valid(self, form):
        if self.request.user.is_authenticated():
            form.save(self.request.user)
        else:
            form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        self.object = self.get_object()
        return reverse('newsletter_detail', kwargs={'pk': self.object.pk})


class NewsletterDetailView(View):
    def get(self, request, *args, **kwargs):
        view = NewsletterDisplayView.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = NewsletterFormView.as_view()
        return view(request, *args, **kwargs)


class NewsletterRawDetailView(DetailView):
    model = Newsletter
    template_name = 'courriers/newsletterraw_detail.html'

    def get_context_data(self, **kwargs):
        context = super(NewsletterRawDetailView, self).get_context_data(**kwargs)

        context['items'] = self.object.items.all()

        return context


class NewsletterUnsubscribeView(FormView):
    template_name = 'courriers/newsletter_unsubscribe.html'
    form_class = UnsubscriptionForm
    model = Newsletter
    context_object_name = 'newsletter'

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        self.object = self.get_object()
        return reverse('newsletter_detail', kwargs={'pk': self.object.pk})


def send_newsletter(request, newsletter_id):
    from courriers.backends import get_backend

    backend_klass = get_backend()
    backend = backend_klass()

    newsletter = get_object_or_404(Newsletter, pk=newsletter_id)
    backend.send_mails(newsletter)

    messages.success(request, _('This newsletter has been sent.'))
    return HttpResponseRedirect(reverse('admin:courriers_newsletter_change', args=(newsletter.id,)))
