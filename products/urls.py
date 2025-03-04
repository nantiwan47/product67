from django.urls import path
from .views import product_detail, add_to_cart, update_cart, delete_cart, cart_detail, search_results, home, checkout, \
    order_status_view, user_logout, register, user_login, profile, edit_profile

urlpatterns = [
    path('', home, name='home'),

    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('profile/', profile, name='profile'),
    path('edit_profile/', edit_profile, name='edit_profile'),

    path('search/', search_results, name='search_results'),
    path('product/<int:pk>/', product_detail, name='product_detail'),

    path('cart/', cart_detail, name='cart'),
    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('update-cart/<int:pk>/', update_cart, name='update_cart'),
    path('delete-cart/<int:pk>/', delete_cart, name='delete_cart'),

    path("checkout/", checkout, name="checkout"),
    path('order-status/', order_status_view, name='order_status'),

]
