from django.contrib.auth.forms import UserCreationForm
from django import forms

from .models import User, Order, Product


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'category', 'price', 'stock', 'image_url']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'category': forms.Select(),
        }

# class OrderUpdateForm(forms.ModelForm):
#     class Meta:
#         model = Order
#         fields = ['status']