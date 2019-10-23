from django.shortcuts import render


def login(request):
    return(request, 'auction/login.html')


def home(request):
    return(request, 'auction/home.html')

