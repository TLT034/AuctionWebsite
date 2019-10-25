from django.urls import path
from . import views

app_name = 'auction'
urlpatterns = [
    path('', views.login, name='login'),
    path('forgot', views.forgot, name='forgot'),
    path('reset_password', views.reset_password, name='reset_password'),
    path('signup', views.signup, name='signup'),
    path('home', views.home, name='home'),
    path('create_auction', views.create_auction, name='create_auction'),
    path('enter_local_code', views.enter_local_code, name='enter_local_code'),
]