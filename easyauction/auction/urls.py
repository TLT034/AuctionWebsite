from django.urls import path
from . import views

app_name = 'auction'
urlpatterns = [
    path('', views.login, name='login'),
    path('home', views.home, name='home'),
    path('create_auction', views.create_auction, name='create_auction'),
    path('enter_local_code', views.enter_local_code, name='enter_local_code'),
]