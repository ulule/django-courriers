# -*- coding: utf-8 -*-
from django.views.generic import View, ListView, DetailView, FormView
from django.views.generic.detail import SingleObjectMixin

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from .models import Newsletter
from .forms import SubscriptionForm


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
