# -*- coding: utf-8 -*-
from django.views.generic import View, ListView, DetailView, FormView
from django.views.generic.edit import FormMixin
from django.views.generic.detail import SingleObjectMixin
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from .models import Newsletter, NewsletterSubscriber, NewsletterList
from .forms import SubscriptionForm, UnsubscribeForm


class NewsletterListDetailView(ListView):
    model = Newsletter
    context_object_name = 'newsletters'
    template_name = 'courriers/newsletter_list.html'

    @cached_property
    def newsletter_list(self):
        return get_object_or_404(NewsletterList, slug=self.kwargs.get('slug'))

    def get_queryset(self):
        return self.newsletter_list.newsletters.status_online().order_by('published_at')


class NewsletterDisplayView(DetailView):
    model = Newsletter
    context_object_name = 'newsletter'
    template_name = 'courriers/newsletter_detail.html'

    def get_context_data(self, **kwargs):
        context = super(NewsletterDisplayView, self).get_context_data(**kwargs)

        context['form'] = SubscriptionForm(user=self.request.user,
                                           newsletter_list=self.model.newsletter_list)

        return context


class NewsletterFormView(SingleObjectMixin, FormView):
    template_name = 'courriers/newsletter_detail.html'
    form_class = SubscriptionForm
    model = Newsletter
    context_object_name = 'newsletter'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(NewsletterFormView, self).post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(NewsletterFormView, self).get_context_data(**kwargs)
        context.update(SingleObjectMixin.get_context_data(self, **kwargs))
        return context

    def get_form_kwargs(self):
        return dict(super(NewsletterFormView, self).get_form_kwargs(), **{
            'newsletter_list': self.object.newsletter_list
        })

    def form_valid(self, form):
        if self.request.user.is_authenticated():
            form.save(self.request.user)
        else:
            form.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return self.object.get_absolute_url()


class NewsletterDetailView(View):
    def get(self, request, *args, **kwargs):
        view = NewsletterDisplayView.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = NewsletterFormView.as_view()
        return view(request, *args, **kwargs)


class NewsletterRawDetailView(DetailView):
    model = Newsletter
    template_name = 'courriers/newsletter_raw_detail.html'

    def get_context_data(self, **kwargs):
        context = super(NewsletterRawDetailView, self).get_context_data(**kwargs)

        context['items'] = self.object.items.all()

        return context


class NewsletterListUnsubscribeView(FormMixin, DetailView):
    template_name = 'courriers/newsletter_unsubscribe.html'
    form_class = UnsubscribeForm
    model = NewsletterSubscriber
    context_object_name = 'newsletter_list'
    success_url = reverse_lazy('newsletter_list')

    def get_initial(self):
        initial = super(NewsletterListUnsubscribeView, self).get_initial()

        if self.kwargs.get('email'):
            initial['email'] = self.kwargs.get('email')

        return initial.copy()

    def get_form_kwargs(self):
        return dict(super(NewsletterListUnsubscribeView, self).get_form_kwargs(), **{
            'newsletter_list': self.object
        })

    def get_context_data(self, **kwargs):
        context = super(NewsletterListUnsubscribeView, self).get_context_data(**kwargs)
        form_class = self.get_form_class()
        context['form'] = self.get_form(form_class)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)

        return self.form_invalid(form)

    def form_valid(self, form):
        form.save()

        return super(NewsletterListUnsubscribeView, self).form_valid(form)


class NewslettersUnsubscribeView(DetailView, FormMixin):
    template_name = 'courriers/newsletters_unsubscribe.html'
    form_class = UnsubscribeAllForm
    model = NewsletterSubscriber
    context_object_name = 'newsletters'
    success_url = reverse_lazy('newsletter_list')

    def get_initial(self):
        initial = super(NewslettersUnsubscribeView, self).get_initial()

        if self.kwargs.get('email'):
            initial['email'] = self.kwargs.get('email')

        return initial.copy()

    def get_context_data(self, **kwargs):
        context = super(NewslettersUnsubscribeView, self).get_context_data(**kwargs)
        form_class = self.get_form_class()
        context['form'] = self.get_form(form_class)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if form.is_valid():
            return self.form_valid(form)

        return self.form_invalid(form)

    def form_valid(self, form):
        # Here, we would record the user's interest using the message
        # passed in form.cleaned_data['message']
        return super(NewslettersUnsubscribeView, self).form_valid(form)
