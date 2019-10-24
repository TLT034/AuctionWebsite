from django.contrib.auth.forms import UserCreationForm
from django import forms


# Default UserCreationForm with added user attributes
class CompleteUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=20)
    last_name = forms.CharField(min_length=1)