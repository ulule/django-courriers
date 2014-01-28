# -*- coding: utf-8 -*-
from django.views.generic import ListView, DetailView, FormView, TemplateView
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.views.generic.base import TemplateResponseMixin
from django.utils.translation import get_language

from .settings import PAGINATE_BY
from .models import Newsletter, NewsletterList
from .forms import SubscriptionForm, UnsubscribeForm
from .utils import ajaxify_template_var


class AJAXResponseMixin(TemplateResponseMixin):
    ajax_template_name = None

    def get_template_names(self):
        names = super(AJAXResponseMixin, self).get_template_names()

        if self.request.is_ajax():
            if self.ajax_template_name:
                names = [self.ajax_template_name] + names
            else:
                names = ajaxify_template_var(names) + names
        return names


class NewsletterListView(AJAXResponseMixin, ListView):
    model = Newsletter
    context_object_name = 'newsletters'
    template_name = 'courriers/newsletter_list.html'
    paginate_by = PAGINATE_BY

    def dispatch(self, *args, **kwargs):
        self.lang = kwargs.get('lang', None) or get_language()

        return super(NewsletterListView, self).dispatch(*args, **kwargs)

    @cached_property
    def newsletter_list(self):
        return get_object_or_404(NewsletterList.objects.has_lang(self.lang),
                                 slug=self.kwargs.get('slug'))

    def get_queryset(self):
        return (self.newsletter_list.newsletters
                .status_online()
                .has_lang(self.lang)
                .order_by('-published_at'))

    def get_context_data(self, **kwargs):
        context = super(NewsletterListView, self).get_context_data(**kwargs)
        context['newsletter_list'] = self.newsletter_list
        return context


class NewsletterDetailView(AJAXResponseMixin, DetailView):
    model = Newsletter
    context_object_name = 'newsletter'
    template_name = 'courriers/newsletter_detail.html'

    def get_queryset(self):
        return self.model.objects.status_online().has_lang(get_language())

    def get_context_data(self, **kwargs):
        context = super(NewsletterDetailView, self).get_context_data(**kwargs)

        context['newsletter_list'] = self.object.newsletter_list

        return context


class BaseNewsletterListFormView(AJAXResponseMixin, FormView):
    model = NewsletterList
    context_object_name = 'newsletter_list'

    @cached_property
    def object(self):
        slug = self.kwargs.get('slug', None)

        if slug:
            return get_object_or_404(self.model, slug=slug)

        return None

    def post(self, request, *args, **kwargs):
        self.get_context_data(**kwargs)

        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if form.is_valid():
            return self.form_valid(form)

        return self.form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super(BaseNewsletterListFormView, self).get_form_kwargs()

        if self.object:
            kwargs['newsletter_list'] = self.object

        return kwargs

    def get_context_data(self, **kwargs):
        context = super(BaseNewsletterListFormView, self).get_context_data(**kwargs)

        if self.object:
            context[self.context_object_name] = self.object

        return context

    def form_valid(self, form):
        if self.request.user.is_authenticated():
            form.save(self.request.user)
        else:
            form.save()

        return HttpResponseRedirect(self.get_success_url())


class NewsletterListSubscribeView(BaseNewsletterListFormView):
    template_name = 'courriers/newsletter_list_subscribe_form.html'
    form_class = SubscriptionForm

    def get_success_url(self):
        return reverse('newsletter_list_subscribe_done')


class NewsletterRawDetailView(AJAXResponseMixin, DetailView):
    model = Newsletter
    template_name = 'courriers/newsletter_raw_detail.html'

    def get_context_data(self, **kwargs):
        context = super(NewsletterRawDetailView, self).get_context_data(**kwargs)

        context['items'] = self.object.items.all()

        for item in context['items']:
            item.newsletter = self.object

        return context


class NewsletterListUnsubscribeView(BaseNewsletterListFormView):
    template_name = 'courriers/newsletter_list_unsubscribe.html'

    def get_form_class(self):
        return UnsubscribeForm

    def get_initial(self):
        initial = super(NewsletterListUnsubscribeView, self).get_initial()
        email = self.request.GET.get('email', None)

        if email:
            initial['email'] = email

        return initial.copy()

    def get_success_url(self):
        if self.object:
            return reverse('newsletter_list_unsubscribe_done',
                           kwargs={'slug': self.object.slug})

        return reverse('newsletter_list_unsubscribe_done')


class NewsletterListUnsubscribeDoneView(AJAXResponseMixin, TemplateView):
    template_name = "courriers/newsletter_list_unsubscribe_done.html"
    model = NewsletterList
    context_object_name = 'newsletter_list'

    def get_context_data(self, **kwargs):
        context = super(NewsletterListUnsubscribeDoneView, self).get_context_data(**kwargs)

        slug = self.kwargs.get('slug', None)

        if slug:
            context[self.context_object_name] = get_object_or_404(self.model, slug=slug)

        return context


class NewsletterListSubscribeDoneView(AJAXResponseMixin, TemplateView):
    template_name = "courriers/newsletter_list_subscribe_done.html"
    model = NewsletterList
    context_object_name = 'newsletter_list'
