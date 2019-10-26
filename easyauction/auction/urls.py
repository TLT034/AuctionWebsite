from django.urls import path
import django.contrib.auth.views as auth_views
from django.urls import reverse_lazy
from django.views.generic.base import RedirectView
from django.contrib.auth.decorators import login_required
from easyauction.decorators import anon_required
from . import views

app_name = 'auction'
urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='auction/account/temp_login.html', redirect_authenticated_user=True),
         name='login'),
    path('logout/', login_required(auth_views.logout_then_login), name='logout'),
    path('signup/', anon_required(views.SignUpView.as_view()), name='signup'),
    path('account/', login_required(views.EditAccountView.as_view()), name='account'),
    path('forgot/', views.forgot, name='forgot'),
    path('reset_password/', views.reset_password, name='reset_password'),
    path('', RedirectView.as_view(url=reverse_lazy('home'))),
    path('home/', login_required(views.home), name='home'),
    path('create_auction/', login_required(views.create_auction), name='create_auction'),
    path('enter_local_code/', login_required(views.enter_local_code), name='enter_local_code')
]
# TODO: add change password
# TODO: add password recovery
