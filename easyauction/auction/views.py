from django.urls import reverse_lazy
from django.views import generic
from .models import AuctionUser
from django.shortcuts import render
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse

from .forms import AuctionForm
from .forms import UserSignUpForm

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
    all_hosted_auctions = Auction.objects.order_by('name')
    all_joined_auctions = Auction.objects.order_by('name')
    return render(request, 'auction/home.html', context={'my_auctions': all_hosted_auctions, 'joined_auctions': all_joined_auctions})


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
    


def enter_local_code(request):
    return render(request, 'auction/enter_local_code.html', context={})
 