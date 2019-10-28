from .forms import auth as auth_forms
from django.urls import reverse_lazy
from django.views import generic
from .models import AuctionUser
from django.shortcuts import render
from .models import Auction, User, Item


# Presents sign up form and submits
class SignUpView(generic.CreateView):
    model = AuctionUser
    form_class = auth_forms.UserSignUpForm
    success_url = reverse_lazy('auction:login')
    template_name = 'auction/account/temp_signup.html'


class ViewAccountView(generic.DetailView):
    model = AuctionUser
    template_name = 'auction/account/temp_account.html'

    def get_object(self):
        return self.request.user


# Presents form for editing select account info
class EditAccountView(generic.UpdateView):
    model = AuctionUser
    fields = ('email', 'first_name', 'last_name')
    template_name = 'auction/account/temp_edit_account.html'
    success_url = reverse_lazy('auction:account')

    def get_object(self):
        return self.request.user


def login(request):
    return render(request, 'auction/login.html', context={})


def forgot(request):
    return render(request, 'auction/forgot.html', context={})


def reset_password(request):
    return render(request, 'auction/reset_password.html', context={})


def signup(request):
    return render(request, 'auction/signup.html', context={})


def home(request):
    all_hosted_auctions = Auction.objects.order_by('name')
    all_joined_auctions = Auction.objects.order_by('name')
    return render(request, 'auction/home.html', context={})  # TODO delete this line once there is an auction url and page
    return render(request, 'auction/home.html', context={'my_auctions': all_hosted_auctions, 'joined_auctions': all_joined_auctions})


def create_auction(request):
    return render(request, 'auction/create_auction.html', context={})


def enter_local_code(request):
    return render(request, 'auction/enter_local_code.html', context={})

