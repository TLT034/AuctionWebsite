import decimal
import io
import os

from django.urls import reverse_lazy
from django.views import generic
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponseForbidden, Http404, FileResponse
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import authenticate, login

import json
from decimal import Decimal
from datetime import datetime

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

    def form_valid(self, form):
        form.save()
        username = self.request.POST['username']
        password = self.request.POST['password1']
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return redirect('auction:login')


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
    context = {
        'user': user,
        'notifications': user.notification_set.order_by('-timestamp')
    }
    return render(request, 'auction/home.html', context=context)


def auctions(request):
    user = request.user
    hosted_auctions = user.auction_set.order_by('-time_created')
    joined_auctions = user.joined_auctions.order_by('-time_created')

    context = {
        'hosted_auctions': hosted_auctions,
        'joined_auctions': joined_auctions,
    }

    # Join auction
    if request.method == 'POST':
        auction_code = request.POST['auction_code']
        try:
            if auction_code:
                auction = Auction.objects.get(pk=auction_code)
                if auction.published:
                    auction.participants.add(user)
                    auction.save()
                else:
                    error_msg = 'This auction has not been published'
                    context['error_msg'] = error_msg
                    return render(request, 'auction/auctions.html', context=context)
            else:
                error_msg = 'Please enter auction code before clicking JOIN'
                context['error_msg'] = error_msg
                return render(request, 'auction/auctions.html', context=context)
        except Auction.DoesNotExist:
            error_msg = 'Invalid auction code'
            context['error_msg'] = error_msg
            return render(request, 'auction/auctions.html', context=context)
        return redirect('auction:auction_detail', auction.id)
    return render(request, 'auction/auctions.html', context=context)


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
        'user_is_admin': user_is_admin,
        'total_participants': auction.participants.count()
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

    return render(request, 'auction/item.html', context={'item': item, 'admin': admin, 'user': user})


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

        auction_type = request.POST.get('auction_type', default=item.auction_type)
        if auction_type != item.auction_type:
            item.winner = None
            item.is_sold = False
            item.is_open = False
            item.current_price = item.starting_price
            while item.bid_set.count() > 0:
                item.bid_set.first().delete()
            item.auction_type = auction_type
            item.save()

        if item.starting_price > item.current_price:
            item.current_price = item.starting_price

        if item.bid_set.count() > 0:
            item.min_bid = float(item.current_price) + float(item.bid_increment)
        else:
            item.min_bid = item.starting_price

        # for live items
        if item.auction_type == 'live':
            final_price = request.POST.get('final_price')
            if final_price:
                item.current_price = final_price

            winner = request.POST.get('winner')
            if winner:
                item.winner = AuctionUser.objects.get(username=winner)
                item.is_sold = True
                item.is_open = False

        item.save()

    return redirect('auction:item', item.id)


def delete_item(request, item_id):
    try:
        item = Item.objects.get(pk=item_id)
        auction_id = item.auction.id
    except Item.DoesNotExist:
        raise Http404("The item you are trying to delete does not exist or may have already been deleted")

    if request.method == 'POST':
        highest_bid = item.bid_set.order_by('-price')[0]
        highest_bid.bidder.possible_balance -= highest_bid.price
        highest_bid.bidder.save()
        item.delete()

    return redirect('auction:auction_detail', auction_id)


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
        prev_bid = item.bid_set.all().order_by('-price')[1]
        item.current_price = prev_bid.price

        item.min_bid = item.current_price + item.bid_increment
        # For the previous bidder, add his original bid to his possible balance
        prev_bid.bidder.possible_balance += prev_bid.price
        prev_bid.bidder.save()

        # For the user whose bid is being deleted, reset his possible balance
        bid.bidder.possible_balance -= bid.price
        bid.bidder.save()

        bid.delete()
        item.save()
    elif item.bid_set.count() == 1:
        # For the user whose bid is being deleted, reset his possible balance
        bid.bidder.possible_balance -= bid.price
        bid.bidder.save()
        item.current_price = item.starting_price
        item.min_bid = item.starting_price
        bid.delete()
        item.save()

    # if the item was sold then we needed to change the winner
    if item.is_sold:
        if item.bid_set.count() > 0:
            item.winner = item.bid_set.latest('price').bidder
        else:
            item.winner = None
            item.is_sold = False
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
            if item.is_open:
                if Bid.objects.count() == 0 or bid_amount >= item.min_bid:
                    bid = Bid(item=item, bidder=user, price=bid_amount)
                    bid.save()

                    item.current_price = bid_amount
                    item.min_bid = item.current_price + item.bid_increment
                    item.save()

                    # update possible balance for new highest bidder
                    user.possible_balance += bid.price
                    user.save()

                    if item.bid_set.count() > 1:
                        # update possible balance for previous highest bidder
                        prev_highest_bid = item.bid_set.order_by('-price')[1]
                        prev_highest_bid.bidder.possible_balance -= prev_highest_bid.price
                        prev_highest_bid.bidder.save()

                        # send outbid notification to previous highest bidder
                        text = f"Outbid! You have been outbid on the {item}"
                        prev_highest_bid.bidder.send_notification(text, item)

                    return render(request, 'auction/bid_success.html', context={'bid': bid})

        return render(request, 'auction/bid_fail.html', context={'bid': {'item': item, 'price': bid_amount}})
    # if not a post, then just redirect to item
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

    include_images = 'include_images' in request.POST

    num_rows = 4
    num_cols = 2

    if include_images:
        num_rows = 2
        num_cols = 2

    block_width = x_res / num_cols
    block_height = y_res / num_rows

    image_width = 170
    image_height = 170
    qr_width = 130
    qr_height = 130
    text_size = 20
    space_between = (block_height - qr_height - text_size) / 3

    if include_images:
        space_between = (block_height - image_height - qr_height - text_size) / 4

    index = 0

    # Draw divider lines on first page
    for r in range(1, num_rows):
        for c in range(1, num_cols):
            p.line(c * block_width, 0, c * block_width, y_res)
            p.line(0, r * block_height, x_res, r * block_height)

    p.setFont("Times-Roman", text_size)

    for item in auction.item_set.all():
        if index != 0 and index % (num_rows * num_cols) == 0:
            # Change to new page, draw divider lines, and reset font
            p.showPage()

            for r in range(1, num_rows):
                for c in range(1, num_cols):
                    p.line(c * block_width, 0, c * block_width, y_res)
                    p.line(0, r * block_height, x_res, r * block_height)

            p.setFont("Times-Roman", text_size)

        # Generate QR code from item page URL
        page_url = request.build_absolute_uri(reverse('auction:item', args=(item.id, )))

        qrw = QrCodeWidget(page_url) 
        b = qrw.getBounds()

        w = b[2] - b[0] 
        h = b[3] - b[1] 

        d = Drawing()
        d.add(qrw)

        # Bottom left corner of block
        x_offset = (index % num_cols) * block_width
        y_offset = (num_rows - 1 - (index // num_cols) % num_rows) * block_height

        # Draw QR code
        d.translate(x_offset + block_width / 2 - qr_width / 2, y_offset + space_between)

        d.scale(qr_width / w, qr_height / h)

        renderPDF.draw(d, p, 1, 1)

        # Draw item name
        p.drawCentredString(x_offset + block_width / 2, y_offset + block_height - text_size - space_between, item.name)

        if include_images:
            # Draw item image
            p.drawImage(settings.BASE_DIR + item.image.url,
                x_offset + x_res / 4 - image_width / 2, y_offset + qr_height + 2 * space_between,
                image_width, image_height)

        index += 1

    p.save()

    buffer.seek(0)

    # Return rendered PDF file
    return FileResponse(buffer, as_attachment=True, filename='QR Codes Printout.pdf')


class MyBidListView(generic.ListView):
    model = Bid

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)

        # Incredibly janky and non-extensible. Should be done with an API call in the future
        filters = [{'text': 'Winning Bids', 'value': 'winning'},
                   {'text': 'Won Bids', 'value': '{"won": "True"}'},
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
            if filtering_json == 'winning':
                user_winning_bids_ids = []
                for bid in queryset:
                    winning_bid = bid.item.bid_set.last()
                    if bid == winning_bid:
                        user_winning_bids_ids.append(bid.pk)
                filtered_queryset = queryset.filter(pk__in=user_winning_bids_ids)
            else:
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


class WatchedItemsView(generic.ListView):
    model = Item

    def get_queryset(self):
        user = self.request.user
        queryset = self.model.objects.filter(pk__in=user.watched_items.all())

        return queryset


def publish(request, pk):
    try:
        auction = Auction.objects.get(pk=pk)
    except Auction.DoesNotExist:
        raise Http404("The auction you are trying to publish does not exist or may have been deleted")

    if request.method == "POST":

        # un-assign winners
        for item in auction.item_set.filter(auction_type='silent'):
            if item.bid_set.count() > 0:
                item.bid_set.order_by('-price')[0].won = False
                item.is_sold = False
                item.winner = None
                item.save()

        # reset guaranteed balance
        for user in auction.participants.all():
            user.guaranteed_balance = 0.00

        auction.publish()
        auction.save()

    return redirect("auction:auction_detail", pk)


def archive(request, pk):
    try:
        auction = Auction.objects.get(pk=pk)
    except Auction.DoesNotExist:
        raise Http404("The auction you are trying to archive does not exist or may have been deleted")

    if request.method == "POST":

        # assign winners
        for item in auction.item_set.filter(auction_type='silent'):
            if item.bid_set.count() > 0:
                # Assign winner
                item.is_sold = True
                item.winner = item.bid_set.latest('price').bidder
                item.save()

                # Mark bid as a winning bid
                bid = item.bid_set.latest('price')
                bid.won = True
                bid.save()

                # Update winners balance
                item.winner.guaranteed_balance += bid.price
                item.winner.save()

                # Send notification to winner
                text = f"Congratulations! You won the {item.name}"
                item.winner.send_notification(text=text, item=item)

        auction.close_bidding()
        auction.archive()
        auction.save()

        # csv output file
        file = open("auction_report.csv", "w")
        file.write(f"{auction.name} report\n")
        file.write(f"Auction closed on:, {datetime.now().strftime('%m/%d/%Y %H:%M:%S')}\n\n")
        file.write("Silent Items\n")
        file.write("Item, Buyer Name, Buyer Username, Price\n")
        for item in auction.item_set.filter(auction_type='silent'):
            if item.winner:
                first_name = item.winner.first_name
                last_name = item.winner.last_name
                user_name = item.winner.username
                sell_price = item.current_price
            else:
                first_name = "N/A"
                last_name = " "
                user_name = "N/A"
                sell_price = 0
            file.write(f"{item.name}, {first_name} {last_name}, {user_name}, {sell_price}\n")
        file.write("\nLive Items\n")
        file.write("Item, Buyer Name, Buyer Username, Price\n")
        for item in auction.item_set.filter(auction_type='live'):
            if item.winner:
                first_name = item.winner.first_name
                last_name = item.winner.last_name
                user_name = item.winner.username
                sell_price = item.current_price
            else:
                first_name = "N/A"
                last_name = " "
                user_name = "N/A"
                sell_price = 0
            file.write(f"{item.name}, {first_name} {last_name}, {user_name}, {sell_price}\n")
        file.close()
    return redirect("auction:auction_detail", pk)


def open_bidding(request, auction_id):
    try:
        auction = Auction.objects.get(pk=auction_id)
    except Auction.DoesNotExist:
        raise Http404("The auction you are trying to open does not exist or may have been deleted")

    if request.method == "POST":
        auction.open_bidding()
        auction.save()

    return redirect("auction:auction_detail", auction_id)


def close_bidding(request, auction_id):
    try:
        auction = Auction.objects.get(pk=auction_id)
    except Auction.DoesNotExist:
        raise Http404("The auction you are trying to close does not exist or may have been deleted")

    if request.method == "POST":
        auction.close_bidding()
        auction.save()

    return redirect("auction:auction_detail", auction_id)


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

    context = {'participants': participants_json, 'n_participants': len(participants), 'auction': auction}
    return render(request, 'auction/participants.html', context=context)


def clear_notifications(request, user_id):
    try:
        user = AuctionUser.objects.get(id=user_id)
        user.notification_set.all().delete()
    except AuctionUser.DoesNotExist:
        raise Http404("The user you does not exist or may have been deleted")

    return redirect("auction:home")


def watch_item(request, item_id: int):
    user = request.user
    user.watch_item(pk=item_id)
    user.save()
    return item_view(request, item_id=item_id)


def unwatch_item(request, item_id: int):
    user = request.user
    user.unwatch_item(pk=item_id)
    user.save()
    return item_view(request, item_id=item_id)
