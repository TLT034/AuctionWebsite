from django.urls import reverse_lazy
from django.views import generic
from .models import AuctionUser
from django.shortcuts import render, redirect
from django.utils import timezone
from django.http import HttpResponseRedirect, HttpResponseForbidden, Http404, HttpResponseNotFound
from django.urls import reverse
from django.core import serializers

from .forms import AuctionForm, UserSignUpForm, AddItemForm

from .models import Auction, AuctionUser, Item


# Presents sign up form and submits
class SignUpView(generic.CreateView):
    model = AuctionUser
    form_class = UserSignUpForm
    success_url = reverse_lazy('auction:login')
    template_name = 'auction/account/signup.html'


class ViewAccountView(generic.DetailView):
    model = AuctionUser
    template_name = 'auction/account/account_view.html'

    def get_object(self):
        return self.request.user


# Presents form for editing select account info
class EditAccountView(generic.UpdateView):
    model = AuctionUser
    fields = ('email', 'first_name', 'last_name')
    template_name = 'auction/account/edit_account.html'
    success_url = reverse_lazy('auction:account')

    def get_object(self):
        return self.request.user


def home(request):
    user = request.user
    hosted_auctions = user.auction_set.order_by('-time_created')
    joined_auctions = user.joined_auctions.order_by('-time_created')

    context = {  # Used for data
                'hosted_auctions': hosted_auctions,
                'joined_auctions': joined_auctions}

    return render(request, 'auction/home2.html', context=context)


"""
TODO: add toggle for switching between live and silent auctions.
The toggle could put a flag in the post data, which the view can use to
pick which items to load
"""
def auction_detail(request, pk):
    # Get context items
    user = request.user
    if user.auction_set.filter(pk=pk).exists():
        user_is_admin = True
        auction = user.auction_set.get(pk=pk)
        items = auction.item_set.all()
    elif user.joined_auctions.filter(pk=pk).exists():
        # TODO: implement count-down on items and only show items with positive countdowns
        user_is_admin = False
        auction = user.joined_auctions.get(pk=pk)
        items = auction.item_set.all()
    elif Auction.objects.filter(pk=pk).exists():
        return HttpResponseForbidden()
    else:
        return Http404()

    # Save object from form or create new form to put in context
    if request.method == 'POST':
        item_form = AddItemForm(request.POST, request.FILES)
        if item_form.is_valid():
            item = item_form.save(commit=False)
            item.auction = auction
            item.save()
            return HttpResponseRedirect(reverse('auction:auction_detail', args=[auction.pk]))
    else:
        item_form = AddItemForm()

    context = {
        'auction': auction,
        'items': items,
        'item_form': item_form,
        'user_is_admin': user_is_admin
    }

    return render(request, 'auction/auction_detail.html', context=context)


def create_auction(request):
    if request.method == 'POST':
        auction_form = AuctionForm(request.POST, request.FILES)
        if auction_form.is_valid():
            auction = auction_form.save(commit=False)
            auction.admin = request.user
            auction.save()
            url = reverse('auction:auction_detail', kwargs={'pk': auction_form.instance.pk})
            return HttpResponseRedirect(url)
    else:
        auction_form = AuctionForm()
    return render(request, 'auction/create_auction.html', context={'auction_form': auction_form})


# TODO: add current user as a participant in the auction specified
def enter_local_code(request):
    return render(request, 'auction/enter_local_code.html', context={})


def item_view(request, item_id):
    user = request.user

    try:
        item = Item.objects.get(pk=item_id)
    except Item.DoesNotExist:
        raise Http404("Item does not exist")

    if user.is_admin(item.auction.pk):
        admin = True

    return render(request, 'auction/item.html', context={'item': item, 'admin': admin})


def edit_item(request, item_id):
    try:
        item = Item.objects.get(pk=item_id)
    except Item.DoesNotExist:
        raise Http404("Item does not exist")

    item.name = request.POST.get('name', item.name)
    item.starting_price = request.POST.get('starting_price', item.starting_price)
    item.description = request.POST.get('description', item.description)

    if item.winner:
        new_winner_username = request.POST.get('winner', item.winner.username)
        if new_winner_username != item.winner.username and AuctionUser.objects.get(username=new_winner_username).is_participant():
            item.winner = AuctionUser.objects.get(username=new_winner_username)

    item.save()

    return redirect('auction:item', item.id)
