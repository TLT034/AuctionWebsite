from django.shortcuts import render
from .models import Auction, User, Item


def login(request):
    return render(request, 'auction/login.html', context={})


def home(request):
    all_hosted_auctions = Auction.objects.order_by('name')
    all_joined_auctions = Auction.objects.order_by('name')
    return render(request, 'auction/home.html', context={})  # TODO delete this line once there is an auction url and page
    return render(request, 'auction/home.html', context={'my_auctions': all_hosted_auctions, 'joined_auctions': all_joined_auctions})


def create_auction(request):
    return render(request, 'auction/create_auction.html', context={})


def enter_local_code(request):
    return render(request, 'auction/enter_local_code.html', context={})

