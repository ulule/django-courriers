#-*- coding: utf-8 -*-
import six

from django.core import exceptions

try:
    from importlib import import_module
except ImportError:
    from django.utils.importlib import import_module


CLASS_PATH_ERROR = 'django-courriers is unable to interpret settings value for %s. '\
                   '%s should be in the form of a tupple: '\
                   '(\'path.to.models.Class\', \'app_label\').'


def load_class(class_path, setting_name=None):
    """
    Loads a class given a class_path. The setting value may be a string or a
    tuple.

    The setting_name parameter is only there for pretty error output, and
    therefore is optional
    """
    if not isinstance(class_path, six.string_types):
        try:
            class_path, app_label = class_path
        except:
            if setting_name:
                raise exceptions.ImproperlyConfigured(CLASS_PATH_ERROR % (
                    setting_name, setting_name))
            else:
                raise exceptions.ImproperlyConfigured(CLASS_PATH_ERROR % (
                    'this setting', 'It'))

    try:
        class_module, class_name = class_path.rsplit('.', 1)
    except ValueError:
        if setting_name:
            txt = '%s isn\'t a valid module. Check your %s setting' % (
                class_path, setting_name)
        else:
            txt = '%s isn\'t a valid module.' % class_path
        raise exceptions.ImproperlyConfigured(txt)

    try:
        mod = import_module(class_module)
    except ImportError as e:
        if setting_name:
            txt = 'Error importing backend %s: "%s". Check your %s setting' % (
                class_module, e, setting_name)
        else:
            txt = 'Error importing backend %s: "%s".' % (class_module, e)

        raise exceptions.ImproperlyConfigured(txt)

    try:
        clazz = getattr(mod, class_name)
    except AttributeError:
        if setting_name:
            txt = ('Backend module "%s" does not define a "%s" class. Check'
                   ' your %s setting' % (class_module, class_name,
                                         setting_name))
        else:
            txt = 'Backend module "%s" does not define a "%s" class.' % (
                class_module, class_name)
        raise exceptions.ImproperlyConfigured(txt)
    return clazz


def ajaxify_template_var(template_var):
    if isinstance(template_var, (list, tuple)):
        template_var = type(template_var)(ajaxify_template_name(name) for name in template_var)
    elif isinstance(template_var, basestring):
        template_var = ajaxify_template_name(template_var)
    return template_var


def ajaxify_template_name(name):
    if "." in name:
        name = "%s-ajax.%s" % tuple(name.rsplit('.', 1))
    else:
        name += "-ajax"
    return name
