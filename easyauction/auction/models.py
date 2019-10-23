from django.db import models

from random import randrange

class Auction(models.Model):
	name = models.CharField(max_length=200)
	time_created = models.DateTimeField()
	entry_code = models.IntegerField(default=randrange(100000))
	published = models.BooleanField(default=False)

	def __str__(self):
		return self.name

