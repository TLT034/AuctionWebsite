from .forms import auth as auth_forms
from django.urls import reverse_lazy
from django.views import generic
from .models import AuctionUser


# TODO: add account successfully created notification before redirecting
# Presents sign up form and submits
class SignUpView(generic.CreateView):
    model = AuctionUser
    form_class = auth_forms.UserSignUpForm
    success_url = reverse_lazy('auction:login')
    template_name = 'auction/account/signup.html'


# TODO: add account successfully updated notificaiton before redirecting
# Presents form for editing select account info
class EditAccountView(generic.UpdateView):
    model = AuctionUser
    fields = ('email', 'first_name', 'last_name')
    template_name = 'auction/account/account.html'
    success_url = reverse_lazy('auction:login')

