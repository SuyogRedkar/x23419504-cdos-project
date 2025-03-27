from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import EmailValidator
from .models import Product, InvoiceProduct

HELP_TEXT = "optional"

class StoreSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, validators=[EmailValidator()])
    first_name = forms.CharField(max_length=30, required=False, help_text=HELP_TEXT)
    last_name = forms.CharField(max_length=30, required=False, help_text=HELP_TEXT)

    class Meta:
        """Meta class  for user registration."""
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'first_name', 'last_name')

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return cleaned_data
        
class StoreLoginForm(forms.Form):
    username = forms.CharField(required=True)
    password = forms.CharField(widget=forms.PasswordInput)


class QuantityForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, label="Quantity to Delete")
    
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock']


class AddStockForm(forms.Form):
    # Dropdown to select the existing product
    product_id = forms.ModelChoiceField(queryset=Product.objects.all(), label="Select Product")
    quantity = forms.IntegerField(min_value=1, label="Quantity to Add")
    
class InvoiceForm(forms.ModelForm):
    class Meta:
        model = InvoiceProduct
        fields = ['product', 'quantity']

class InvoiceProductForm(forms.Form):
    customer_name = forms.CharField(max_length=100)
    customer_number = forms.CharField(max_length=15)
    products = forms.ModelMultipleChoiceField(queryset=Product.objects.all(), widget=forms.CheckboxSelectMultiple)
    quantity = forms.IntegerField(min_value=1)