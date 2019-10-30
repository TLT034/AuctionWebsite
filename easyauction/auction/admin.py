from django.contrib import admin
from .models import Auction, Item, AuctionUser

admin.site.register(Auction)
admin.site.register(Item)
admin.site.register(AuctionUser)
