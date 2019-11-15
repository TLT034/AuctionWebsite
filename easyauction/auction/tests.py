from django.test import TestCase
from .models import AuctionUser, Bid
from django.urls import reverse
from .forms import AddItemForm
import time


class AuthTests(TestCase):
    def test_create_account(self):
        """
        Tests that user accounts are successfully created and stored in DB
        """
        username = 'test_user'
        password = 'test12345'
        len1 = len(AuctionUser.objects.filter(username=username))

        create_user(username, password)

        len2 = len(AuctionUser.objects.filter(username=username))

        self.assertEqual(len2 - len1, 1)

    def test_edit_account(self):
        """
        Tests that users can edit their info
        """
        username = 'test_user'
        password = 'test12345'
        email = 'email1@mail.com'
        create_user(username, password, email)
        self.client.login(username=username, password=password)

        email2 = 'email2@mail.com'
        response = self.client.post(reverse('auction:edit_account'), {'email': email2})

        user_email = AuctionUser.objects.get(username=username).email

        self.assertEqual(user_email, email2)

    def test_access_home_logged_in(self):
        """
        Logged in users should be able to access the home page.
        """
        username = 'test_user'
        password = 'test12345'
        create_user(username, password)

        response = self.client.post(reverse('auction:login'), {'username': username, 'password': password})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('auction:home'))

    def test_access_home_not_logged_in(self):
        """
        Anonymous users attempting to access the home page should be redirected to the login page.
        """
        response = self.client.get(reverse('auction:home'))

        self.assertRedirects(response, '/login/?next=/home/')

    def test_access_signup_logged_in(self):
        """
        Logged in users should be redirected to home when they attempt to access the signup page
        """
        username = 'test_user'
        password = 'test12345'
        create_user(username, password)
        self.client.login(username=username, password=password)

        response = self.client.get(reverse('auction:signup'))

        self.assertRedirects(response, '/login/?auction%3Ahome=/signup/', target_status_code=302)

    def test_access_signup_not_logged_in(self):
        """
        Anonymous users should be able to reach the signup page
        """
        response = self.client.get(reverse('auction:signup'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request['PATH_INFO'], reverse('auction:signup'))

    def test_access_change_password_done_page_before_change_password(self):
        """
        Users should get 403 if they attempt to access 'auction:change_password_done' without being referred by
        'auction:change_password'
        """
        username = 'test_user'
        password = 'test12345'
        create_user(username, password)
        self.client.login(username=username, password=password)

        response = self.client.get(reverse('auction:change_password_done'))

        self.assertEqual(response.status_code, 403)

    def test_access_change_password_done_page_after_change_password(self):
        """
        Users should be able to access 'auction:change_password_done' if referred from 'auction:change_password'
        """
        username = 'test_user'
        password = 'test12345'
        create_user(username, password)
        self.client.login(username=username, password=password)

        response = self.client.post(reverse('auction:change_password'), {'old_password': password, 'new_password1': password, 'new_password2': password})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('auction:change_password_done'))


def create_user(username, password, email=None):
    AuctionUser.objects.create_user(username=username, password=password, email=email).save()


class AuctionTests(TestCase):
    def test_restrict_auction_detail_access_to_admins(self):
        # Admin
        username1 = 'admin'
        password1 = 'test12345'
        create_user(username1, password1)
        self.client.login(username=username1, password=password1)
        admin = AuctionUser.objects.get(username=username1)
        admin.create_auction(name='Test Auction')

        auction_pk = admin.auction_set.first().pk
        admin_response = self.client.get(reverse('auction:auction_detail', kwargs={'pk': auction_pk}))
        self.client.logout()

        # Non-participant user
        username2 = 'user'
        password2 = 'test12345'
        create_user(username2, password1)
        self.client.login(username=username2, password=password2)

        user_response = self.client.get(reverse('auction:auction_detail', kwargs={'pk': auction_pk}))
        self.client.logout()

        self.assertEqual(admin_response.status_code, 200)
        self.assertEqual(user_response.status_code, 403)

    def test_correctly_rendered_admin_detail_view(self):
        username = 'test_user'
        password = 'test12345'
        create_user(username, password)

        user = AuctionUser.objects.get(username=username)
        user.create_auction('test auction', 'test auction desc')
        auction = user.auction_set.get(name='test auction')

        # Asserts the page loaded and the add item form rendered for the admin
        self.client.login(username=username, password=password)
        response = self.client.get(reverse('auction:auction_detail', args=[auction.pk]))
        self.assertTrue(response.status_code, 200)
        self.assertTrue('id="add_item_col"' in response.content.decode())


    def test_restrict_auction_detail_access_to_participants(self):
        pass

    def test_correctly_rendered_participant_detail_view(self):
        # Admin
        username1 = 'admin'
        password1 = 'test12345'
        create_user(username1, password1)
        admin = AuctionUser.objects.get(username=username1)
        admin.create_auction(name='Test Auction')

        auction = admin.auction_set.first()
        auction_pk = auction.pk

        # Participant
        username2 = 'user'
        password2 = 'test12345'
        create_user(username2, password1)
        participant = AuctionUser.objects.get(username=username2)
        auction.participants.add(participant)
        self.client.login(username=username2, password=password2)

        # Asserts the user had access to the page and that the add item form didn't render for the non-admin
        response = self.client.get(reverse('auction:auction_detail', kwargs={'pk': auction_pk}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse('id="add_item_col"' in response.content.decode())

    def test_add_item(self):
        username = 'test_user'
        password = 'test12345'
        create_user(username, password)

        user = AuctionUser.objects.get(username=username)
        user.create_auction('test auction', 'test auction desc')
        auction = user.auction_set.get(name='test auction')

        data = {'name': 'test item',
                'starting_price': 5.00,
                'description': 'desc for test item',
                'auction_type': 'silent',
                'bid_increment': 1.00}

        item_form = AddItemForm(data)
        item_form.is_valid()
        item = item_form.save(commit=False)
        item.auction = auction
        item.current_price = item.starting_price
        item.min_bid = item.starting_price
        item.save()

        updated_auction = user.auction_set.get(name='test auction')
        self.assertTrue(updated_auction.item_set.filter(name='test item').exists())

        def test_auction_detail_displays_winner(self):
            # Admin
            username1 = 'admin'
            password1 = 'test12345'
            create_user(username1, password1)
            admin = AuctionUser.objects.get(username=username1)
            admin.create_auction(name='Test Auction')

            auction = admin.auction_set.first()
            auction_pk = auction.pk

            # Participant
            username2 = 'user'
            password2 = 'test12345'
            create_user(username2, password1)
            participant = AuctionUser.objects.get(username=username2)

            # Set participant as item winner
            auction.participants.add(participant)
            auction.add_item(name='test item', starting_price=5, item_desc='test desc')
            auction.save()
            item = auction.item_set.first()
            item.winner = user
            item.is_open = False
            item.is_sold = True
            item.save()

            # Test that the item correctly renders the winner
            self.client.login(username=username2, password=password2)
            response = self.client.get(reverse('auction:auction_detail', args=auction.pk))
            self.assertContains(response, 'Winner: user', status_code=200)


class BidTests(TestCase):
    def test_render_no_bids(self):
        username = 'test_user'
        password = 'test12345'
        create_user(username, password)

        self.client.login(username=username, password=password)
        response = self.client.get(reverse('auction:my_bids'))

        s = "<v-card-title>You haven't placed any bids yet.</v-card-title>"
        self.assertContains(response, s, status_code=200)

    def test_default_filters(self):
        # Admin
        username1 = 'admin'
        password1 = 'test12345'
        create_user(username1, password1)

        # Create auction and add items
        admin = AuctionUser.objects.get(username=username1)
        admin.create_auction(name='test auction', description='desc')
        auction = admin.auction_set.first()
        auction.add_item(name='test item 1', item_desc='desc', starting_price=5)
        item1 = auction.item_set.get(pk=1)
        auction.add_item(name='test item 2', item_desc='desc', starting_price=5)
        item2 = auction.item_set.get(pk=2)

        # Bidder
        username2 = 'bidder'
        password2 = 'test12345'
        create_user(username2, password2)
        bidder = AuctionUser.objects.get(username=username2)

        # Bid on two items
        bid1 = Bid(price=10, bidder=bidder, item=item1)
        bid1.save()
        time.sleep(1)
        bid2 = Bid(price=10, bidder=bidder, item=item2)
        bid2.save()

        # Verify that more recent bid is displayed first (bid2 is newer so it should be displayed first)
        self.client.login(username=username2, password=password2)
        data = {'filter': '',
                'order': ''}
        response = self.client.get(reverse('auction:my_bids'), data=data)
        queryset = response.context['object_list']
        self.assertTrue(queryset[0].timestamp > queryset[1].timestamp and queryset[0].pk == bid2.pk)

    def test_won_filter(self):
        # Admin
        username1 = 'admin'
        password1 = 'test12345'
        create_user(username1, password1)

        # Create auction and add items
        admin = AuctionUser.objects.get(username=username1)
        admin.create_auction(name='test auction', description='desc')
        auction = admin.auction_set.first()
        auction.add_item(name='test item 1', item_desc='desc', starting_price=5)
        item1 = auction.item_set.get(pk=1)
        auction.add_item(name='test item 2', item_desc='desc', starting_price=5)
        item2 = auction.item_set.get(pk=2)

        # Bidder
        username2 = 'bidder'
        password2 = 'test12345'
        create_user(username2, password2)
        bidder = AuctionUser.objects.get(username=username2)

        # Bid on two items
        bid1 = Bid(price=10, bidder=bidder, item=item1)
        bid1.save()
        time.sleep(1)
        bid2 = Bid(price=10, bidder=bidder, item=item2)
        bid2.save()

        # Make bidder the winner of item 1
        bid1.won = True
        bid1.save()
        item1.winner = bidder
        item1.save()

        # Verify that only the won item is displayed
        self.client.login(username=username2, password=password2)
        data = {'filter': '{"won": "True"}',
                'order': ''}
        response = self.client.get(reverse('auction:my_bids'), data=data)
        queryset = response.context['object_list']
        print('QUERYSET', queryset)
        self.assertTrue(len(queryset) == 1 and queryset[0].pk == item1.pk)

    def test_open_filter(self):
        # Admin
        username1 = 'admin'
        password1 = 'test12345'
        create_user(username1, password1)

        # Create auction and add items
        admin = AuctionUser.objects.get(username=username1)
        admin.create_auction(name='test auction', description='desc')
        auction = admin.auction_set.first()
        auction.add_item(name='test item 1', item_desc='desc', starting_price=5)
        item1 = auction.item_set.get(pk=1)
        auction.add_item(name='test item 2', item_desc='desc', starting_price=5)
        item2 = auction.item_set.get(pk=2)

        # Bidder
        username2 = 'bidder'
        password2 = 'test12345'
        create_user(username2, password2)
        bidder = AuctionUser.objects.get(username=username2)

        # Bid on two items
        bid1 = Bid(price=10, bidder=bidder, item=item1)
        bid1.save()
        time.sleep(1)
        bid2 = Bid(price=10, bidder=bidder, item=item2)
        bid2.save()

        # Open item 1
        item1.is_open = True
        item1.save()

        # Verify that only the bid on the open item is shown
        self.client.login(username=username2, password=password2)
        data = {'filter': '{"item__is_open": "True"}',
                'order': ''}
        response = self.client.get(reverse('auction:my_bids'), data=data)
        queryset = response.context['object_list']
        self.assertTrue(len(queryset) == 1 and queryset[0].pk == item1.pk)

    def test_order_by_price(self):
        # Admin
        username1 = 'admin'
        password1 = 'test12345'
        create_user(username1, password1)

        # Create auction and add items
        admin = AuctionUser.objects.get(username=username1)
        admin.create_auction(name='test auction', description='desc')
        auction = admin.auction_set.first()
        auction.add_item(name='test item 1', item_desc='desc', starting_price=5)
        item1 = auction.item_set.get(pk=1)
        auction.add_item(name='test item 2', item_desc='desc', starting_price=5)
        item2 = auction.item_set.get(pk=2)

        # Bidder
        username2 = 'bidder'
        password2 = 'test12345'
        create_user(username2, password2)
        bidder = AuctionUser.objects.get(username=username2)

        # Bid on two items
        bid1 = Bid(price=20, bidder=bidder, item=item1)
        bid1.save()
        time.sleep(1)
        bid2 = Bid(price=10, bidder=bidder, item=item2)
        bid2.save()

        # Verify that higher bid is displayed first
        self.client.login(username=username2, password=password2)
        data = {'filter': '',
                'order': '-price'}
        response = self.client.get(reverse('auction:my_bids'), data=data)
        queryset = response.context['object_list']
        self.assertTrue(queryset[0].price > queryset[1].price)

    def test_filter_order_combination(self):
        # Admin
        username1 = 'admin'
        password1 = 'test12345'
        create_user(username1, password1)

        # Bidder
        username2 = 'bidder'
        password2 = 'test12345'
        create_user(username2, password2)
        bidder = AuctionUser.objects.get(username=username2)

        # Create auction and add items
        admin = AuctionUser.objects.get(username=username1)
        admin.create_auction(name='test auction', description='desc')
        auction = admin.auction_set.first()
        auction.add_item(name='test item 1', item_desc='desc', starting_price=1)
        item1 = auction.item_set.get(pk=1)
        auction.add_item(name='test item 2', item_desc='desc', starting_price=1)
        item2 = auction.item_set.get(pk=2)
        auction.add_item(name='test item 3', item_desc='desc', starting_price=1)
        item3 = auction.item_set.get(pk=3)
        auction.add_item(name='test item 4', item_desc='desc', starting_price=1)
        item4 = auction.item_set.get(pk=4)

        # Bid on the items
        bid1 = Bid(price=10, bidder=bidder, item=item1)
        bid1.save()
        time.sleep(1)
        bid2 = Bid(price=5, bidder=bidder, item=item2)
        bid2.save()
        bid3 = Bid(price=5, bidder=bidder, item=item3)
        bid3.save()
        bid4 = Bid(price=5, bidder=bidder, item=item4)
        bid4.save()

        # Make bidder the winner of items 1 and 2
        bid1.won = True
        bid1.save()
        item1.winner = bidder
        item1.save()
        bid2.won = True
        bid2.save()
        item2.winner = bidder
        item2.save()

        # Verify that only the won items are displayed ordered by price
        self.client.login(username=username2, password=password2)
        data = {'filter': '{"won": "True"}',
                'order': '-price'}
        response = self.client.get(reverse('auction:my_bids'), data=data)
        queryset = response.context['object_list']
        self.assertTrue(len(queryset) == 2 and queryset[0].item.winner.pk == bidder.pk and queryset[0].price > queryset[1].price)
