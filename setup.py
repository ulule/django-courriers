# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages

version = __import__('courriers').__version__

root = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(root, 'README.rst')) as f:
    README = f.read()

setup(
    name='django-courriers',
    version=version,
    description='A generic application to manage your newsletters',
    long_description=README,
    author='Florent Messa',
    author_email='florent.messa@gmail.com',
    url='http://github.com/ulule/django-courriers',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        "django-separatedvaluesfield",
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities',
    ]
)
