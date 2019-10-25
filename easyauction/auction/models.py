from django.db import models

from random import randrange

# Dummy User model. When you replace this, edit the ForeignKey in the Item model.
class User(models.Model):
	name = models.CharField(max_length=200)

	def __str__(self):
		return self.name

def random_entry_code():
	return randrange(100000)

class Auction(models.Model):
	name = models.CharField(max_length=200)
	time_created = models.DateTimeField()
	entry_code = models.IntegerField(default=random_entry_code)
	published = models.BooleanField(default=False)

	def __str__(self):
		return self.name


class Item(models.Model):
	name = models.CharField(max_length=200)
	starting_price = models.FloatField()
	item_desc = models.TextField('item description')
	is_sold = models.BooleanField(default=False)
	is_paid = models.BooleanField(default=False)
	is_open = models.BooleanField(default=False)
	paid_time = models.DateTimeField(null=True, blank=True)
	auction = models.ForeignKey(Auction, on_delete=models.CASCADE)
	winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

	def __str__(self):
		return self.name