from django import template
from products.models import CartItem

register = template.Library()

@register.filter
def cart_count(user):
    """ ดึงจำนวนสินค้าทั้งหมดในตระกร้าของผู้ใช้ """
    if user.is_authenticated:
        cart_items = CartItem.objects.filter(cart__user=user)
        return sum(item.quantity for item in cart_items)
    return 0
