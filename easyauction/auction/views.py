from django.shortcuts import render
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse

from .forms import AuctionForm
from .models import Auction


def login(request):
    return render(request, 'auction/login.html', context={})


def home(request):
	return render(request, 'auction/home.html', context={})


def auction_detail(request, pk):
	auction = Auction.objects.all().filter(pk=pk).first()
	return render(request, 'auction/auction_detail.html', context={'auction': auction})


def create_auction(request):
	if request.method == 'POST':
		form = AuctionForm(request.POST)
		if form.is_valid():
			new_auction = Auction(name=form.cleaned_data['auction_name'], time_created=timezone.now())
			new_auction.save()
			url = reverse('auction:auction-detail', kwargs={'pk': new_auction.pk})
			return HttpResponseRedirect(url)
	else:
		form = AuctionForm()

	return render(request, 'auction/create_auction.html', context={'form': form})