from django.contrib import admin

from .models import Auction, Item, User

admin.site.register(Auction)
admin.site.register(Item)
admin.site.register(User)