from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms


# Default UserCreationForm with added user attributes
class UserSignUpForm(UserCreationForm):
    first_name = forms.CharField(min_length=1, max_length=20, label='First name')
    last_name = forms.CharField(min_length=1, max_length=20, label='Last name')
    email = forms.EmailField(label='Email')

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
