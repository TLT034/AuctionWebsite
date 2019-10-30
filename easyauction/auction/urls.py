from django.urls import path
from . import views

app_name = 'auction'
urlpatterns = [
    path('', views.login, name='login'),
    path('home', views.home, name='home'),
    path('create-auction', views.create_auction, name='create-auction'),
    path('auction-detail/<int:pk>', views.auction_detail, name='auction-detail')
]