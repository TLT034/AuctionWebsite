from django.contrib.auth.decorators import user_passes_test
from django.urls import resolve
from django.http import HttpResponseForbidden
from urllib import parse
import functools


def anon_required(function=None, redirect_field_name='auction:home'):
    """
    Decorator for views that checks that the user is not logged in.
    Based off of @login_required decorator
    :param function: function should return true if user passes entry test
    :param redirect_field_name: redirect in case user fails test
    :return: allows access on pass, redirects on fail. If no function is passed, returns the constructed decorator
    """
    actual_decorator = user_passes_test(
        lambda user: user.is_anonymous,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def redirected_from(referer):
    def wrapper(func):
        def inner_wrapper(request, *args, **kwargs):
            if 'HTTP_REFERER' in request.META and parse.urlparse(request.META['HTTP_REFERER']).path == referer:
                return func(request, *args, **kwargs)
            else:
                return HttpResponseForbidden()

        return inner_wrapper
    return wrapper
