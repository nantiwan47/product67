from django.contrib import admin
from .models import User, Product, Cart, CartItem, Order, OrderItem

from django.contrib.auth.admin import UserAdmin

class UserAdmin(UserAdmin):
    model = User
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('username',)

admin.site.register(User, UserAdmin)

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_category_display', 'price', 'stock', 'created_at')

    def get_category_display(self, obj):
        return dict(Product.CATEGORY_CHOICES).get(obj.category, obj.category)

    get_category_display.short_description = 'Category'

admin.site.register(Product)

# Register the Cart model
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at')
    search_fields = ('user__username',)
    ordering = ('-created_at',)

admin.site.register(Cart, CartAdmin)

# Register the CartItem model
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity')
    search_fields = ('cart__user__username', 'product__name')
    ordering = ('cart', 'product')

admin.site.register(CartItem, CartItemAdmin)

admin.site.register(Order)
admin.site.register(OrderItem)