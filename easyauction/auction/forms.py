from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms

from .models import AuctionUser, Item, Auction


class AuctionForm(forms.ModelForm):
    class Meta:
        model = Auction
        fields = ['name', 'image', 'description']


# Default UserCreationForm with added user attributes
class UserSignUpForm(UserCreationForm):
    first_name = forms.CharField(min_length=1, max_length=20, label='First name')
    last_name = forms.CharField(min_length=1, max_length=20, label='Last name')
    email = forms.EmailField(label='Email')

    class Meta(UserCreationForm.Meta):
        model = AuctionUser
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')


class AddItemForm(forms.ModelForm):
    auction_type = forms.ChoiceField(choices=Item.AUCTION_TYPES)

    class Meta:
        model = Item
        fields = ['name', 'starting_price', 'bid_increment', 'description', 'image', 'auction_type']
