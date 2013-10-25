django-courriers
================

A generic application to manage your newsletters

What it does?
-------------

django-courriers has three models:

- ``Newsletter`` which represents a newsletter.
- ``NewsletterItem`` an item of a newsletter. It could be a content-type you want.
- ``NewsletterSubscriber`` which represents a user who is subscribed to a newsletter.


You have the choice between three backends to manage and send your emails:

- ``SimpleBackend``, a simple backend to send emails with Django and
  your current smtp configuration
- ``MailchimpBackend``, a `Mailchimp`_ backend which uses `mailchimp library`_
- ``MailJetBackend``, a `Mailjet`_ backend, which will be available soon


Installation
------------

1. Download the package on GitHub_ or simply install it via PyPi
2. Add ``courriers`` to your ``INSTALLED_APPS`` ::

    INSTALLED_APPS = (
        'courriers',
    )

3. Sync your database using ``syncdb`` command from django command line
4. Configure settings

You have to specify which backend you want to use in your settings ::

    COURRIERS_BACKEND_CLASS = 'courriers.backends.simple.SimpleBackend'

A quick reminder: you can also set your custom ``DEFAULT_FROM_EMAIL`` in Django settings.

Backends
--------

courriers.backends.simple.SimpleBackend
........................................

A simple backend to send your emails with Django and
your current smtp configuration

courriers.backends.mailchimp.MailchimpBackend
..............................................

A backend to manage your newsletters with Mailchimp.


What you need to do for mailchimp
.................................

- Create an account on Mailchimp
- Get your API key
- Add it to your settings with others options as described below
- Install the `mailchimp library`_
- Create a list or more if you have users
  from different countries (see multilingual section below)

Which this backend you have to provide additional settings ::

    COURRIERS_MAILCHIMP_API_KEY = 'You API key'
    COURRIERS_MAILCHIMP_LIST_NAME = 'The name of a list of users'
    COURRIERS_DEFAULT_FROM_NAME = 'Your name'


``COURRIERS_MAILCHIMP_LIST_NAME`` is the default name for lists of subscribers.

Multilingual
............

If you want to send multilingual newsletters you have to create one list
of users per language with the following syntax ::

    [COURRIERS_MAILCHIMP_LIST_NAME]_us-en
    [COURRIERS_MAILCHIMP_LIST_NAME]_fr
    [COURRIERS_MAILCHIMP_LIST_NAME]_es
    [COURRIERS_MAILCHIMP_LIST_NAME]_it
    [COURRIERS_MAILCHIMP_LIST_NAME]_pt-br

Where the suffix language code is one of Django language code.

See `available languages codes`_.

.. _GitHub: https://github.com/ulule/django-courriers
.. _Available languages codes: https://github.com/django/django/tree/master/django/conf/locale
.. _Mailchimp: http://mailchimp.com/
.. _Mailjet: https://eu.mailjet.com/
.. _mailchimp library: https://pypi.python.org/pypi/mailchimp
