from django.urls import path
import django.contrib.auth.views as auth_views
from django.urls import reverse_lazy
from django.views.generic.base import RedirectView
from django.contrib.auth.decorators import login_required
from .decorators import anon_required, redirected_from
from . import views
from easyauction import settings
from django.contrib.staticfiles.urls import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

app_name = 'auction'
urlpatterns = [
    path('', RedirectView.as_view(url=reverse_lazy('auction:home'))),
    path('home/', login_required(views.home), name='home'),
]

# Account management urls
urlpatterns += [
    path('login/', auth_views.LoginView.as_view(template_name='auction/account/login.html',
                                                redirect_authenticated_user=True),
         name='login'),
    path('logout/', login_required(auth_views.logout_then_login),
         name='logout'),
    path('signup/', anon_required(views.SignUpView.as_view()),
         name='signup'),
    path('account/', login_required(views.ViewAccountView.as_view()),
         name='account'),
    path('account/watchlist/', login_required(views.WatchedItemsView.as_view(template_name='auction/watchlist.html')),
         name='watchlist'),
    path('account/edit/', login_required(views.EditAccountView.as_view()),
         name='edit_account'),
    path('account/change_password/', login_required(auth_views.PasswordChangeView.as_view(success_url=reverse_lazy('auction:change_password_done'))),
         name='change_password'),
    path('account/change_password/done/', redirected_from('auction:change_password')(auth_views.PasswordChangeDoneView.as_view(template_name='auction/account/change_password_done.html')),
         name='change_password_done'),
    path('account/reset_password/', auth_views.PasswordResetView.as_view(email_template_name='auction/account/temp_reset_password.html', success_url=reverse_lazy('auction:reset_password_done')),
         name='reset_password'),
    path('account/reset_password/done/', redirected_from('auction:reset_password')(auth_views.PasswordResetDoneView.as_view()),
         name='reset_password_done'),
    path('account/reset_password/confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(success_url=reverse_lazy('auction:reset_password_complete')),
         name='reset_password_confirm'),
    path('account/reset_password/complete/', redirected_from('auction:reset_password_confirm')(auth_views.PasswordResetCompleteView.as_view()),
         name='reset_password_complete'),
]

# Auction management urls
urlpatterns += [
  path('auctions/', login_required(views.auctions), name='auctions'),
  path('auction/create_auction/', login_required(views.create_auction), name='create_auction'),
  path('auction/auction_detail/<int:pk>', login_required(views.auction_detail), name='auction_detail'),
  path('auction/item/<int:item_id>', login_required(views.item_view), name='item'),
  path('auction/edit_item/<int:item_id>', login_required(views.edit_item), name='edit_item'),
  path('auction/delete_item/<int:item_id>', login_required(views.delete_item), name='delete_item'),
  path('auction/item/<int:item_id>/watch_item/', login_required(views.watch_item), name='watch_item'),
  path('auction/item/<int:item_id>/unwatch_item/', login_required(views.unwatch_item), name='unwatch_item'),
  path('auction/item/<int:item_id>/submit_bid/', login_required(views.submit_bid), name='submit_bid'),
  path('auction/item/<int:item_id>/remove_bid/<int:bid_id>', login_required(views.remove_bid), name='remove_bid'),
  path('auction/my_bids', login_required(views.MyBidListView.as_view(template_name='auction/my_bids.html')), name='my_bids'),
  path('auction/auction_detail/<int:pk>/qr_codes', login_required(views.auction_qr_codes), name='auction_qr_codes'),
  path('auction/auction_detail/<int:pk>/publish', login_required(views.publish), name='publish'),
  path('auction/auction_detail/<int:pk>/archive', login_required(views.archive), name='archive'),
  path('auction/auction_detail/<int:auction_id>/open_bidding', login_required(views.open_bidding), name='open_bidding'),
  path('auction/auction_detail/<int:auction_id>/close_bidding', login_required(views.close_bidding), name='close_bidding'),
  path('auction/participants/<int:auction_id>', login_required(views.participants_list), name='participants'),
  path('clear_notifications/<int:user_id>', login_required(views.clear_notifications), name='clear_notifications')
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
