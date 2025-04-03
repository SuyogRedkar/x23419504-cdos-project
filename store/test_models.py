import pytest
from django.contrib.auth.models import User
from .models import Store, Product, Order, Invoice, InvoiceProduct, Transaction


@pytest.mark.django_db
class TestModels:

    @pytest.fixture(autouse=True)
    def setup(self):
        """Create test data for models"""
        self.user = User.objects.create_user(username="testuser", password="testpassword")

        self.store = Store.objects.create(name="Test Store", owner=self.user)

        self.product = Product.objects.create(
            store=self.store,
            name="Test Product",
            description="A sample product",
            price=100.00,
            stock=10
        )

        self.order = Order.objects.create(
            customer_name="John Doe",
            status="Pending"
        )

        self.invoice = Invoice.objects.create(
            store=self.store,
            customer_name="Alice",
            customer_number="1234567890"
        )

        self.invoice_product = InvoiceProduct.objects.create(
            invoice=self.invoice,
            product=self.product,
            quantity=2
        )

        self.transaction = Transaction.objects.create(
            store=self.store,
            invoice=self.invoice,
            customer_name="Alice",
            customer_number="1234567890",
            total_amount=200.00,
            products='[]',
            stripe_session_id="sess_123456"
        )

    def test_store_creation(self):
        """Test if a store is created successfully"""
        assert self.store.name == "Test Store"
        assert self.store.owner.username == "testuser"

    def test_product_creation(self):
        """Test if a product is created successfully"""
        assert self.product.name == "Test Product"
        assert self.product.description == "A sample product"
        assert self.product.price == 100.00
        assert self.product.stock == 10
        assert self.product.store == self.store

    def test_order_creation(self):
        """Test if an order is created successfully"""
        assert self.order.customer_name == "John Doe"
        assert self.order.status == "Pending"

    def test_invoice_creation(self):
        """Test if an invoice is created successfully"""
        assert self.invoice.customer_name == "Alice"
        assert self.invoice.customer_number == "1234567890"
        assert self.invoice.store == self.store

    def test_invoice_product_creation(self):
        """Test if an invoice product entry is created correctly"""
        assert self.invoice_product.invoice.customer_name == "Alice"
        assert self.invoice_product.product.name == "Test Product"
        assert self.invoice_product.quantity == 2
        assert self.invoice_product.total_price == self.product.price * 2

    def test_transaction_creation(self):
        """Test if a transaction is created successfully"""
        assert self.transaction.customer_name == "Alice"
        assert self.transaction.customer_number == "1234567890"
        assert self.transaction.total_amount == 200.00
        assert self.transaction.stripe_session_id == "sess_123456"
        assert self.transaction.get_products() == []  # Initially set as empty list

    def test_transaction_product_json(self):
        """Test storing and retrieving products as JSON in Transaction"""
        self.transaction.set_products([{"product_id": 1, "name": "Test Product"}])
        assert self.transaction.get_products() == [{"product_id": 1, "name": "Test Product"}]
