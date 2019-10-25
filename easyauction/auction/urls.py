from django.urls import path
import django.contrib.auth.views as auth_views
from django.contrib.auth.decorators import login_required
from easyauction.decorators import anon_required
from django.views.generic.base import TemplateView
from . import views

app_name = 'auction'
urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='auction/account/login.html', redirect_authenticated_user=True),
         name='login'),
    path('logout/', login_required(auth_views.logout_then_login), name='logout'),
    path('signup/', anon_required(views.SignUpView.as_view()), name='signup'),
    path('', login_required(TemplateView.as_view(template_name='auction/home.html')), name='home'),
    path('account/<int:pk>', login_required(views.EditAccountView.as_view()), name='account'),
]
# TODO: add decorator to verify user can only edit their own account
# TODO: add change password
# TODO: add password recovery