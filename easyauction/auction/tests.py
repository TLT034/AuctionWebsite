from django.test import TestCase
from .models import AuctionUser
from django.urls import reverse


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
        pass

    def test_restrict_auction_detail_access_to_participants(self):
        pass

    def test_correctly_rendered_participant_detail_view(self):
        pass
