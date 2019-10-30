from django import forms

from .models import Auction


class AuctionForm(forms.Form):
	auction_name = forms.CharField(label="Auction name", max_length=200)