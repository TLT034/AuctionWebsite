# Generated by Django 2.2.6 on 2019-10-31 01:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auction', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='item',
            name='item_desc',
        ),
        migrations.AddField(
            model_name='auction',
            name='description',
            field=models.TextField(default='Auction description'),
        ),
        migrations.AddField(
            model_name='item',
            name='description',
            field=models.TextField(default='Item description'),
        ),
        migrations.AlterField(
            model_name='auction',
            name='time_created',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]