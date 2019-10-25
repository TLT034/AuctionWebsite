from django.shortcuts import render


def login(request):
    return render(request, 'auction/login.html', context={})


def forgot(request):
    return render(request, 'auction/forgot.html', context={})


def reset_password(request):
    return render(request, 'auction/reset_password.html', context={})


def signup(request):
    return render(request, 'auction/signup.html', context={})


def home(request):
    return render(request, 'auction/home.html', context={})


def create_auction(request):
    return render(request, 'auction/create_auction.html', context={})


def enter_local_code(request):
    return render(request, 'auction/enter_local_code.html', context={})

