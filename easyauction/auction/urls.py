from django.urls import path
from . import views

app_name = 'auction'
urlpatterns = [
    path('', views.login, name='login'),
    path('home', views.home, name='home')
]