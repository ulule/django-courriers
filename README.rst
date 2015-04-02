django-courriers
================

.. image:: https://secure.travis-ci.org/ulule/django-courriers.png?branch=master
    :alt: Build Status
    :target: http://travis-ci.org/ulule/django-courriers

A generic application to manage your newsletters

Compatibility
-------------

This library is compatible with:

- python2.6, django1.4
- python2.6, django1.5
- python2.6, django1.6
- python2.7, django1.4
- python2.7, django1.5
- python2.7, django1.6
- python2.7, django1.7
- python2.7, django1.8
- python3.3, django1.5
- python3.3, django1.6
- python3.3, django1.7
- python3.3, django1.8
- python3.4, django1.6
- python3.4, django1.7
- python3.4, django1.8

What it does?
-------------

django-courriers has three models:

- ``NewsletterList`` which represents a newsletter list
- ``Newsletter`` which represents a newsletter
- ``NewsletterItem`` an item of a newsletter. It could be a content-type
- ``NewsletterSubscriber`` which represents a user who is subscribed to a newsletter


You have the choice between three backends to manage and send your emails:

- ``SimpleBackend``, a simple backend to send emails with Django and
  your current smtp configuration
- ``MailchimpBackend``, a `Mailchimp`_ backend which uses `mailchimp library`_
- ``MailJetBackend``, a `Mailjet`_ backend which uses `mailjet library`_


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

courriers.backends.mailjet.MailjetBackend
..............................................

A backend to manage your newsletters with Mailjet.


What you need to do for mailchimp
.................................

- Create an account on Mailchimp
- Get your API key
- Add it to your settings with others options as described below
- Install the `mailchimp library`_
- Create a list or more if you have users
  from different countries

With this backend you have to provide additional settings ::

    COURRIERS_MAILCHIMP_API_KEY = 'Your API key'
    COURRIERS_DEFAULT_FROM_NAME = 'Your name'


What you need to do for mailjet
.................................

- Create an account on Mailjet
- Get your API key and API Secret key
- Add it to your settings with others options as described below
- Install the `mailjet library`_
- Create a list or more if you have users
  from different countries

With this backend you have to provide additional settings ::

    COURRIERS_MAILJET_API_KEY = 'Your API key'
    COURRIERS_MAILJET_API_SECRET_KEY = 'Your API Secret key'
    COURRIERS_DEFAULT_FROM_NAME = 'Your name'

.. _GitHub: https://github.com/ulule/django-courriers
.. _Mailchimp: http://mailchimp.com/
.. _Mailjet: https://eu.mailjet.com/
.. _mailchimp library: https://pypi.python.org/pypi/mailchimp
.. _mailjet library: https://pypi.python.org/pypi/mailjet/
