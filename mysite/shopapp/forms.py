from django import forms
from django.contrib.auth.models import Group
from django.forms import ModelForm

from .models import Product, Order


class GroupForm(ModelForm):
    class Meta:
        model = Group
        fields = ['name']


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('name', 'price', 'description', 'discount', 'preview')

    images = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'multiple': True}),
    )


class OrderForm(forms.Form):
    class Meta:
        model = Order
        fields = ('delivery_address', 'promocode')


class CSVImportForm(forms.Form):
    csv_file = forms.FileField()