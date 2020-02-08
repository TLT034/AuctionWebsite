from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from auction.utils import rotate_image
import os


# Extends the base user class to preserve compatibility with Django's auth backend
# TODO: catch errors
class AuctionUser(AbstractUser):
    guaranteed_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    possible_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

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

    def watch_item(self, pk: int):
        item = Item.objects.get(pk=pk)
        self.watched_items.add(item)

    def unwatch_item(self, pk:int):
        item = Item.objects.get(pk=pk)
        self.watched_items.remove(item)


    def send_notification(self, text, item):
        notification = self.notification_set.create(text=text, item=item)
        return notification


class Auction(models.Model):
    name = models.CharField(max_length=200)
    time_created = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(default="default_item_pic.jpg", upload_to="auction_pics")
    published = models.BooleanField(default=False)
    admin = models.ForeignKey(AuctionUser, on_delete=models.CASCADE)
    description = models.TextField()
    participants = models.ManyToManyField(AuctionUser, related_name='joined_auctions', related_query_name='joined_auction')
    opened_for_bidding = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def publish(self):
        self.published = True

    def archive(self):
        self.published = False

    def open_bidding(self):
        self.opened_for_bidding = True
        for item in self.item_set.all():
            item.is_open = True
            item.save()

    def close_bidding(self):
        self.opened_for_bidding = False
        for item in self.item_set.all():
            item.is_open = False
            item.save()

    def add_item(self, name, starting_price, item_desc):
        item = self.item_set.create(name=name,
                             starting_price=starting_price,
                             current_price=starting_price,
                             min_bid=starting_price,
                             description=item_desc)
        return item

    def remove_item(self, pk):
        self.item_set.filter(pk=pk).first().delete()


class Item(models.Model):
    AUCTION_TYPES = [('silent', 'silent'), ('live', 'live')]

    name = models.CharField(max_length=200)
    starting_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    bid_increment = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    min_bid = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(default="defaults/default_item_pic.jpg", upload_to="item_pics")
    description = models.TextField()
    auction_type = models.CharField(max_length=6, choices=AUCTION_TYPES, default='silent')
    is_sold = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)
    is_open = models.BooleanField(default=False)
    paid_time = models.DateTimeField(null=True, blank=True)
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE)
    winner = models.ForeignKey(AuctionUser, on_delete=models.SET_NULL, null=True, blank=True)
    followers = models.ManyToManyField(AuctionUser, related_name='watched_items', related_query_name='watched_item')

    def __str__(self):
        return self.name


@receiver(post_save, sender=Item, dispatch_uid="update_image_profile")
def update_image(sender, instance, **kwargs):
    if instance.image:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        fullpath = BASE_DIR + instance.image.url
        rotate_image(fullpath)


class Bid(models.Model):
    bidder = models.ForeignKey(AuctionUser, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    won = models.BooleanField(default=False)

    def __str__(self):
        return f'Bid for ${self.price} on item {self.item.name} by user {self.bidder.username}'


class Notification(models.Model):
    user = models.ForeignKey(AuctionUser, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, default=None)
    timestamp = models.DateTimeField(auto_now_add=True)
    text = models.TextField()
