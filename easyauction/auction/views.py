from django.urls import reverse_lazy
from django.views import generic
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponseForbidden, Http404
from django.urls import reverse
import json
from decimal import Decimal

from .forms import AuctionForm, UserSignUpForm, AddItemForm

from .models import Auction, AuctionUser, Item, Bid


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


def auction_detail(request, pk):
    # Get context items
    user = request.user
    if user.auction_set.filter(pk=pk).exists():
        user_is_admin = True
        auction = user.auction_set.get(pk=pk)
        live_items = auction.item_set.filter(auction_type='live')
        silent_items = auction.item_set.filter(auction_type='silent')
    elif user.joined_auctions.filter(pk=pk).exists():
        # TODO: implement count-down on items and only show items with positive countdowns
        user_is_admin = False
        auction = user.joined_auctions.get(pk=pk)
        live_items = auction.item_set.filter(auction_type='live')
        silent_items = auction.item_set.filter(auction_type='silent')
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
            item.current_price = item.starting_price
            item.min_bid = item.starting_price
            item.save()
            return HttpResponseRedirect(reverse('auction:auction_detail', args=[auction.pk]))
    else:
        item_form = AddItemForm()

    context = {
        'auction': auction,
        'live_items': live_items,
        'silent_items': silent_items,
        'total_items': live_items.union(silent_items),
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
    admin = False

    try:
        item = Item.objects.get(pk=item_id)
    except Item.DoesNotExist:
        raise Http404("The item you are trying to view does not exist or may have been deleted")

    if user.is_admin(item.auction.pk):
        admin = True

    # item_bids = Bid.objects.filter(item=item).order_by('-price')

    return render(request, 'auction/item.html', context={'item': item, 'admin': admin})


def edit_item(request, item_id):
    try:
        item = Item.objects.get(pk=item_id)
    except Item.DoesNotExist:
        raise Http404("The item you are trying to edit does not exist or may have been deleted")

    if request.method == 'POST':
        item.name = request.POST.get('name', default=item.name)
        item.starting_price = float(request.POST.get('starting_price', default=item.starting_price))
        item.bid_increment = float(request.POST.get('bid_increment', default=item.bid_increment))
        item.description = request.POST.get('description', default=item.description)

        if item.starting_price > item.current_price:
            item.current_price = item.starting_price

        if item.bid_set.count() > 0:
            item.min_bid = float(item.current_price) + float(item.bid_increment)
        else:
            item.min_bid = item.starting_price

        winner = request.POST.get('winner')
        if winner:
            item.winner = AuctionUser.objects.get(username=winner)

        item.save()

    return redirect('auction:item', item.id)


def remove_bid(request, item_id, bid_id):
    try:
        item = Item.objects.get(pk=item_id)
    except Item.DoesNotExist:
        raise Http404("The item you are trying to remove a bid from does not exist or may have been deleted")
    try:
        bid = Bid.objects.get(pk=bid_id)
    except Bid.DoesNotExist:
        raise Http404("The bid you are trying to remove does not exist or may have already been deleted")

    # if there are more bids than just the one bid that we are deleting
    if bid == item.bid_set.latest('timestamp') and item.bid_set.count() > 1:
        item.current_price = item.bid_set.all().order_by('-price')[1].price
        item.min_bid = item.current_price + item.bid_increment
        bid.delete()
        item.save()
    elif item.bid_set.count() == 1:
        item.current_price = item.starting_price
        item.min_bid = item.starting_price
        bid.delete()
        item.save()

    return redirect('auction:item', item.id)


def submit_bid(request, item_id):
    user = request.user
    try:
        item = Item.objects.get(pk=item_id)
    except Item.DoesNotExist:
        raise Http404("The item you are trying to bid on does not exist or may have been deleted")

    if request.method == 'POST':
        bid_amount = Decimal(request.POST.get('bid', -1))

        if bid_amount != -1:
            if Bid.objects.count() == 0 or bid_amount >= item.min_bid:
                bid = Bid(item=item, bidder=user, price=bid_amount)
                bid.save()

                item.current_price = bid_amount
                item.min_bid = item.current_price + item.bid_increment
                item.save()
                return render(request, 'auction/bid_success.html', context={'bid': bid})

        return render(request, 'auction/bid_fail.html', context={'bid': {'item': item, 'price': bid_amount}})
    # if not a post, then just redirect to item
    return redirect('auction:item', item.id)


class MyBidListView(generic.ListView):
    model = Bid

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)

        filters = [{'text': 'Winning Bids', 'value': '{"won": "True"}'},
                   {'text': 'Open Bids', 'value': '{"item__is_open": "True"}'}]
        context['filters'] = filters
        orderings = [{'text': 'Date', 'value': '-timestamp'},
                     {'text': 'Price', 'value': '-price'}]
        context['orderings'] = orderings

        return context

    def get_queryset(self):
        user = self.request.user
        queryset = self.model.objects.filter(bidder__pk=user.pk)

        filtering_json = self.request.GET.get('filter', None)
        if filtering_json:
            filtering = json.loads(filtering_json)
            filtered_queryset = queryset.filter(**filtering)
        else:
            filtered_queryset = queryset.filter()

        ordering = self.request.GET.get('order', '-timestamp')
        if ordering:
            ordered_queryset = filtered_queryset.order_by(ordering, '-timestamp')
        else:
            ordered_queryset = filtered_queryset.order_by('-timestamp')

        return ordered_queryset

def publish(request, pk):
    try:
        auction = Auction.objects.get(pk=pk)
    except Auction.DoesNotExist:
        raise Http404("The auction you are trying to publish does not exist or may have been deleted")

    if request.method == "POST":
        auction.publish()
        auction.save()

    return redirect("auction:auction_detail", pk)


def archive(request, pk):
    try:
        auction = Auction.objects.get(pk=pk)
    except Auction.DoesNotExist:
        raise Http404("The auction you are trying to archive does not exist or may have been deleted")

    if request.method == "POST":
        auction.archive()
        auction.save()

    return redirect("auction:auction_detail", pk)

def participants_list(request, auction_id):
    # Get auction
    try:
        auction = Auction.objects.get(id=auction_id)
        if auction.admin.pk != request.user.pk:
            return HttpResponseForbidden()
    except Auction.DoesNotExist:
        return Http404()

    if request.method == 'GET':
        # Get participants based on filter
        if 'filter' in request.GET and request.GET['filter'] == 'true':
            won_items = auction.item_set.exclude(winner=None)
            participants = set()
            for item in won_items:
                if item.winner not in participants:
                    participants.add(item.winner)
        else:
            participants = auction.participants.all()
    else:
        participants = auction.participants.all()

    # Build list of participant json objects to be rendered by v-data-table
    participant_objs = []
    for participant in participants:
        items_won = auction.item_set.filter(winner__id=participant.id)
        participant_obj = {'name': participant.username,
                            'id': participant.id,
                            'items_won': list(map(lambda x: x['name'], items_won.values('name'))),
                            'total_cost': 0}
        for item in items_won:
            participant_obj['total_cost'] += float(item.current_price)
        participant_objs.append(participant_obj)

    participants_json = json.dumps(participant_objs)

    context = {'participants': participants_json, 'n_participants': len(participants)}
    return render(request, 'auction/participants.html', context=context)
