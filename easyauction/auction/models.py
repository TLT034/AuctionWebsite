from django.db import models
from random import randrange

# Need to validate that the random number is unique (not already in use by another auction)
def random_entry_code():
	return randrange(100000)


# Dummy User model. When you replace this, edit the ForeignKey
# in the Item model and the registration in admin.py.
class User(models.Model):
	name = models.CharField(max_length=200)

	def __str__(self):
		return self.name



class Auction(models.Model):
	name = models.CharField(max_length=200)
	time_created = models.DateTimeField()
	entry_code = models.IntegerField(default=random_entry_code)
	published = models.BooleanField(default=False)

	def __str__(self):
		return self.name

	def publish(self):
		self.published = True
		return self.entry_code

	def archive(self):
		self.published = False

	def add_item(self, name, starting_price, item_desc):
		self.item_set.create(name=name, starting_price=starting_price, item_desc=item_desc)

	def remove_item(self, pk):
		self.item_set.filter(pk=pk).first().delete()



class Item(models.Model):
	name = models.CharField(max_length=200)
	starting_price = models.DecimalField(max_digits=10, decimal_places=2)
	main_pic = models.ImageField(default="default_item_pic.jpg", upload_to="item_pics")
	item_desc = models.TextField("item description")
	is_sold = models.BooleanField(default=False)
	is_paid = models.BooleanField(default=False)
	is_open = models.BooleanField(default=False)
	paid_time = models.DateTimeField(null=True, blank=True)
	auction = models.ForeignKey(Auction, on_delete=models.CASCADE)
	winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

	def __str__(self):
		return self.name