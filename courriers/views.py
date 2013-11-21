# -*- coding: utf-8 -*-
from django.views.generic import View, ListView, DetailView, FormView, TemplateView
from django.views.generic.edit import FormMixin
from django.views.generic.detail import SingleObjectMixin
from django.core.urlresolvers import reverse_lazy, reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from .models import Newsletter, NewsletterList
from .forms import SubscriptionForm, UnsubscribeForm, UnsubscribeAllForm


class NewsletterListView(ListView):
    model = Newsletter
    context_object_name = 'newsletters'
    template_name = 'courriers/newsletter_list.html'
    paginate_by = 3

    @cached_property
    def newsletter_list(self):
        return get_object_or_404(NewsletterList, slug=self.kwargs.get('slug'))

    def get_queryset(self):
        if self.kwargs.get('lang'):
            return self.newsletter_list.newsletters \
                                       .status_online() \
                                       .filter(languages__contains=self.kwargs.get('lang')) \
                                       .order_by('published_at')
        return self.newsletter_list.newsletters.status_online().order_by('published_at')

    def get_context_data(self, **kwargs):
        context = super(NewsletterListView, self).get_context_data(**kwargs)
        context['slug'] = self.newsletter_list.slug
        return context


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
    model = NewsletterList
    context_object_name = 'newsletter_list'
    success_url = reverse_lazy('newsletter_list')

    def get_initial(self):
        initial = super(NewsletterListUnsubscribeView, self).get_initial()
        email = self.request.GET.get('email', None)

        if email:
            initial['email'] = email

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

    def get_success_url(self):
        return reverse('unsubscribe_list_thanks', kwargs={'slug': self.object.slug})


class NewslettersUnsubscribeView(FormView):
    template_name = 'courriers/newsletters_unsubscribe.html'
    form_class = UnsubscribeAllForm
    success_url = reverse_lazy('unsubscribe_thanks')

    def get_initial(self):
        initial = super(NewslettersUnsubscribeView, self).get_initial()
        email = self.request.GET.get('email', None)

        if email:
            initial['email'] = email

        return initial.copy()

    def form_valid(self, form):
        form.save()
        return super(NewslettersUnsubscribeView, self).form_valid(form)


class UnsubscribeListThanksView(TemplateView):
    template_name = "courriers/unsubscribe_list_thanks.html"

    def get_context_data(self, **kwargs):
        context = super(UnsubscribeListThanksView, self).get_context_data(**kwargs)
        newsletter_list_slug = kwargs.pop('slug')
        newsletter_list = get_object_or_404(NewsletterList, slug=newsletter_list_slug)
        context['newsletter_list_name'] = newsletter_list.name
        return context


class UnsubscribeAllThanksView(TemplateView):
    template_name = "courriers/unsubscribe_thanks.html"

    def get_context_data(self, **kwargs):
        return super(UnsubscribeAllThanksView, self).get_context_data(**kwargs)
