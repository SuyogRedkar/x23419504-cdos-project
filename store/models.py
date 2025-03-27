# models.py
from django.db import models
import json

class Store(models.Model):
    name = models.CharField(max_length=100)
    owner = models.OneToOneField('auth.User', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Product(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()

    def __str__(self):
        return self.name

class Order(models.Model):
    customer_name = models.CharField(max_length=100)
    date_created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Shipped', 'Shipped')])

    def __str__(self):
        return f"Order #{self.id}"
        
class Invoice(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    customer_name = models.CharField(max_length=100)
    customer_number = models.CharField(max_length=15)
    products = models.ManyToManyField(Product, through='InvoiceProduct')

    def __str__(self):
        return f"Invoice for {self.customer_name}"
    
class InvoiceProduct(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        # Calculate total price when saving
        self.total_price = self.product.price * self.quantity
        super().save(*args, **kwargs)
        

class Transaction(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True)
    invoice = models.ForeignKey("Invoice", on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=255)
    customer_number = models.CharField(max_length=50)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    products = models.TextField()
    stripe_session_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def set_products(self, products_list):
        self.products = json.dumps(products_list)

    def get_products(self):
        return json.loads(self.products)

    def __str__(self):
        return f"Transaction {self.id} - {self.customer_name}"
