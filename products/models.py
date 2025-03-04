from django.db import models
from django.contrib.auth.models import AbstractUser

def upload_to(instance, filename):
    return f"product/{instance.category}/{filename}"

class User(AbstractUser):
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    profile_image = models.ImageField(upload_to='profile/', blank=True, null=True, default='profile/default_profile.jpg')

class Product(models.Model):
    CATEGORY_CHOICES = (
        ('consumer_goods', 'สินค้าอุปโภคบริโภค'),
        ('beverages', 'เครื่องดื่ม'),
        ('snacks', 'ขนมขบเคี้ยวและของกินเล่น'),
        ('household_items', 'ของใช้ในครัวเรือน'),
        ('personal_items', 'ของใช้ส่วนตัว'),
        ('general_items', 'ของใช้ทั่วไป'),
        ('frozen_items', 'สินค้าแช่เย็นและแช่แข็ง'),
        ('cigarettes_alcohol', 'บุหรี่และเครื่องดื่มแอลกอฮอล์'),
    )

    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    price = models.IntegerField()
    stock = models.IntegerField()
    image_url = models.ImageField(upload_to=upload_to)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart {self.id} for {self.user.username}"

    # รวมราคาสินค้าทั้งหมดใน cart ของ user นั้นๆ
    def get_total_price(self):
        return sum(item.total_item_price() for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} of {self.product.name} in Cart {self.cart.id}"

    def total_item_price(self):
        return self.quantity * self.product.price

class Order(models.Model):
    STATUS_CHOICES = (
        ('preparing', 'กำลังเตรียมสินค้า'),
        ('ready', 'พร้อมรับสินค้า'),
        ('completed', 'สำเร็จ'),
        ('cancelled', 'ยกเลิก')
    )

    PAYMENT_METHODS = (
        ('transfer', 'โอนเงิน'),
        ('cash', 'เงินสด'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='preparing')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS)
    slip_image = models.ImageField(upload_to='slips/', blank=True, null=True)
    pickup_time = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.IntegerField()
