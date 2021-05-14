from django import forms
# this is the model used when we add a product to the cart
from .models import OrderItem


class AddToCartForm(forms.ModelForm):

    class Meta:
        model = OrderItem
        fields = ['quantity']
