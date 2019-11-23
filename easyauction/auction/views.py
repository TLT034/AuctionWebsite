import decimal
import io
import os

from django.urls import reverse_lazy
from django.views import generic
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponseForbidden, Http404, FileResponse
from django.urls import reverse
from django.conf import settings

import json
from decimal import Decimal

from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing 
from reportlab.graphics.barcode.qr import QrCodeWidget 
from reportlab.graphics import renderPDF
from reportlab.lib.pagesizes import letter

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
    if bid == item.bid_set.latest('timestamp'):
        print("\nTrue\n")
    else:
        print("\nFalse\n")
    if bid == item.bid_set.latest('timestamp') and item.bid_set.count() > 1:
        item.current_price = item.bid_set.all().order_by('-timestamp')[1].price
        item.min_bid = item.current_price + item.bid_increment
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
            bid = Bid(item=item, bidder=user, price=bid_amount)
            bid.save()

            item.current_price = bid_amount
            item.min_bid = item.current_price + item.bid_increment
            item.save()

    return redirect('auction:item', item.id)


def auction_qr_codes(request, pk):
    user = request.user
    admin = False

    try:
        auction = Auction.objects.get(pk=pk)
    except Auction.DoesNotExist:
        raise Http404("The auction you are trying to view does not exist or may have been deleted")

    if user.is_admin(auction.pk):
        admin = True

    buffer = io.BytesIO()

    # 612.0 x 792.0 (letter size)
    p = canvas.Canvas(buffer, pagesize=letter)
    x_res = 612
    y_res = 792

    image_width = 170
    image_height = 170
    qr_width = 130
    qr_height = 130
    text_size = 20
    space_between = (y_res / 2 - image_height - qr_height - text_size) / 4

    index = 0

    p.line(306, 0, 306, 792)
    p.line(0, 396, 612, 396)
    p.setFont("Times-Roman", text_size)

    for item in auction.item_set.all():
        if index != 0 and index % 4 == 0:
            p.showPage()
            p.line(306, 0, 306, 792)
            p.line(0, 396, 612, 396)
            p.setFont("Times-Roman", text_size)

        page_url = request.build_absolute_uri(reverse('auction:item', args=(item.id, )))

        qrw = QrCodeWidget(page_url) 
        b = qrw.getBounds()

        w = b[2] - b[0] 
        h = b[3] - b[1] 

        d = Drawing()
        d.add(qrw)

        x_offset = x_res / 2
        if index & 1 == 0:
            x_offset = 0

        y_offset = 0
        if index & 2 == 0:
            y_offset = y_res / 2

        index += 1

        d.translate(x_offset + x_res / 4 - qr_width / 2, y_offset + space_between)

        d.scale(qr_width / w, qr_height / h)

        renderPDF.draw(d, p, 1, 1)

        p.drawCentredString(x_offset + x_res / 4, y_offset + qr_height + image_height + 3 * space_between, item.name)

        p.drawImage(settings.BASE_DIR + item.image.url,
            x_offset + x_res / 4 - image_width / 2, y_offset + qr_height + 2 * space_between,
            image_width, image_height)

    p.save()

    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename='QR Codes Printout.pdf')


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
