from django.contrib.auth.decorators import user_passes_test


def anon_required(function=None, redirect_field_name='auction:home'):
    """
    Decorator for views that checks that the user is not logged in.
    Based off of @login_required decorator
    """
    actual_decorator = user_passes_test(
        lambda user: user.is_anonymous,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
