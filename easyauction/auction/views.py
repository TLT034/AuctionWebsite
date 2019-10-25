from django.shortcuts import render


def login(request):
    return render(request, 'auction/login.html', context={})


def home(request):
    return render(request, 'auction/home.html', context={})


def create_auction(request):
    return render(request, 'auction/create_auction.html', context={})


def enter_local_code(request):
    return render(request, 'auction/enter_local_code.html', context={})

