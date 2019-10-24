from .forms import auth as auth_forms
from django.urls import reverse_lazy
from django.views import generic


class SignUpView(generic.CreateView):
    form_class = auth_forms.CompleteUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'easyauction/templates/registration/signup.html'
