from django.db import models
from random import randrange
from django.contrib.auth.models import AbstractUser


# TODO: Validate that the random number is unique (not already in use by another auction)
def random_entry_code():
    return randrange(10000)


# Extends the base user class to preserve compatibility with Django's auth backend
class AuctionUser(AbstractUser):
    # Creates auction setting the current user as admin
    def create_auction(self, name: str, description: str = None):
        if description:
            self.auction_set.create(name=name, description=description)
        else:
            self.auction_set.create(name=name)

    # Retrieves specified auction, returning None if it does not exist
    def get_auction(self, pk: int):
        auction = self.auction_set.get(pk=pk)
        return auction

    def has_auction(self, pk: int):
        try:
            self.auction_set.get(pk=pk)
        except AuctionUser.DoesNotExist:
            return False
        else:
            return True

    def is_admin(self, pk: int = None):
        if pk:
            return self.auction_set.filter(pk=pk).exists()
        else:
            return self.auction_set.filter(published=True).exists()

    def is_participant(self):
        return self.joined_auctions.exists()

    def archive_auction(self, pk: int):
        auction = self.get_auction(pk=pk)
        auction.archive()


class Auction(models.Model):
    name = models.CharField(max_length=200)
    time_created = models.DateTimeField(auto_now_add=True)
    entry_code = models.IntegerField(default=random_entry_code)
    image = models.ImageField(default="default_item_pic.jpg", upload_to="auction_pics")
    published = models.BooleanField(default=False)
    admin = models.ForeignKey(AuctionUser, on_delete=models.CASCADE)
    description = models.TextField()
    participants = models.ManyToManyField(AuctionUser, related_name='joined_auctions', related_query_name='joined_auction')

    def __str__(self):
        return self.name

    def publish(self):
        self.published = True
        return self.entry_code

    def archive(self):
        self.published = False

    def add_item(self, name, starting_price, item_desc):
        self.item_set.create(name=name, starting_price=starting_price, description=item_desc)

    def remove_item(self, pk):
        self.item_set.filter(pk=pk).first().delete()


class Item(models.Model):
	AUCTION_TYPES = [('silent', 'silent'), ('live', 'live')]

	name = models.CharField(max_length=200)
	starting_price = models.DecimalField(max_digits=10, decimal_places=2)
	image = models.ImageField(default="defaults/default_item_pic.jpg", upload_to="item_pics")
	description = models.TextField()
	auction_type = models.CharField(max_length=6, choices=AUCTION_TYPES, default='silent')
	is_sold = models.BooleanField(default=False)
	is_paid = models.BooleanField(default=False)
	is_open = models.BooleanField(default=False)
	paid_time = models.DateTimeField(null=True, blank=True)
	auction = models.ForeignKey(Auction, on_delete=models.CASCADE)
	winner = models.ForeignKey(AuctionUser, on_delete=models.SET_NULL, null=True, blank=True)

	def __str__(self):
	    return self.name
