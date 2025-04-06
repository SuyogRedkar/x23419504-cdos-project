from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
import stripe
from django.urls import reverse
from django.conf import settings
from django.http import JsonResponse
from django.db.models import Sum
from datetime import datetime
from django.template.loader import render_to_string
from weasyprint import HTML
from django.http import HttpResponse
import tempfile
from .forms import StoreSignUpForm,StoreLoginForm, QuantityForm, ProductForm, AddStockForm, InvoiceForm, InvoiceProductForm
from .models import Product, Order,Invoice, InvoiceProduct,Transaction


stripe.api_key = settings.STRIPE_SECRET_KEY

def store_sign_up(request):
    if request.method == "POST":
        form = StoreSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            un = form.cleaned_data.get('username')
            messages.success(request, 'Account created for {}.'.format(un))
            return redirect("store_login")
    elif request.method == "GET":
        form = StoreSignUpForm()
    return render(request, 'signup.html', {'form': form})

def store_login(request):
    if request.method == "POST":
        form = StoreLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome, {username}!')
                return redirect("dashboard")
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = StoreLoginForm()
    
    return render(request, 'login.html', {'form': form})
    
def store_logout(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("store_login")
    
    
def dashboard(request):
    all_products = Product.objects.all() 
    context = {
        'all_products': all_products,
    }
    return render(request, 'dashboard.html', context)
    
def delete_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    # Handle the form submission when the user specifies a quantity to delete
    if request.method == 'POST':
        form = QuantityForm(request.POST)
        if form.is_valid():
            quantity_to_delete = form.cleaned_data['quantity']
            if quantity_to_delete > 0 and quantity_to_delete <= product.stock:
                product.stock -= quantity_to_delete  # Reduce the stock by the specified quantity
                product.save()
                return redirect('dashboard')  # Redirect to the dashboard after updating the product stock
            else:
                # Handle case when quantity is invalid
                form.add_error('quantity', 'Invalid quantity. Please enter a valid amount to delete.')
    else:
        form = QuantityForm()

    return render(request, 'delete_product.html', {'form': form, 'product': product})
    
def edit_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('dashboard')  # Redirect to the dashboard after saving the changes
    else:
        form = ProductForm(instance=product)

    return render(request, 'edit_product.html', {'form': form})
    
def add_product(request):
    if request.method == 'POST':
        # Form for adding stock
        add_stock_form = AddStockForm(request.POST)
        product_form = ProductForm(request.POST)

        if 'add_stock' in request.POST and add_stock_form.is_valid():
            product = add_stock_form.cleaned_data['product_id']
            quantity = add_stock_form.cleaned_data['quantity']

            try:
                # Use the product object itself to access the ID, then add stock
                product.stock += quantity
                product.save()
                messages.success(request, f'Successfully added {quantity} to {product.name}.')
            except Product.DoesNotExist:
                messages.error(request, 'Product not found.')
            return redirect('add_product')
        
        elif 'add_new_product' in request.POST and product_form.is_valid():
            product_form.save()
            messages.success(request, 'New product added successfully!')
            return redirect('add_product')
    else:
        add_stock_form = AddStockForm()
        product_form = ProductForm()

    return render(request, 'add_product.html', {
        'add_stock_form': add_stock_form,
        'product_form': product_form
    })
    
def makebill(request):
    if request.method == 'POST':
        customer_name = request.POST.get('customer_name')
        customer_number = request.POST.get('customer_number')
        product_ids = request.POST.getlist('product')
        quantities = request.POST.getlist('quantity')

        errors = []

        # Begin the transaction
        with transaction.atomic():
            # Create invoice
            invoice = Invoice.objects.create(customer_name=customer_name, customer_number=customer_number)

            for product_id, quantity in zip(product_ids, quantities):
                product = Product.objects.get(id=product_id)
                quantity = int(quantity)

                if quantity > product.stock:
                    errors.append(f"Not enough stock for {product.name}. Available: {product.stock}, Requested: {quantity}")
                    # Rollback the transaction if an error occurs
                    transaction.set_rollback(True)
                else:
                    # Update stock quantity
                    product.stock -= quantity
                    product.save()

                    # Add the product to the invoice
                    InvoiceProduct.objects.create(invoice=invoice, product=product, quantity=quantity)

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'invoice.html', {'products': Product.objects.all()})

        return redirect('invoice_detail', invoice_id=invoice.id)

    products = Product.objects.all()
    return render(request, 'invoice.html', {'products': products})
    
def invoice_detail(request, invoice_id):
    # Retrieve the invoice object using the given invoice_id
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    # Fetch the associated products (with quantities and prices)
    invoice_products = invoice.invoiceproduct_set.all()

    total_price = sum(item.total_price for item in invoice_products)

    return render(request, 'invoice_detail.html', {'invoice': invoice, 'invoice_products': invoice_products, 'total_price': total_price,"stripe_public_key": settings.STRIPE_PUBLIC_KEY,})
    
def create_checkout_session(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    invoice_products = InvoiceProduct.objects.filter(invoice=invoice)  # Assuming a reverse relation exists

    line_items = [
        {
            "price_data": {
                "currency": "usd",
                "product_data": {"name": item.product.name},
                "unit_amount": int(item.product.price * 100),  # Convert to cents
            },
            "quantity": item.quantity,
        }
        for item in invoice_products
    ]

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=line_items,
        mode="payment",
        success_url = request.build_absolute_uri(reverse("payment_success")) + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url = request.build_absolute_uri(reverse("payment_cancel")),
        metadata={"invoice_id": str(invoice.id)},
    )

    return JsonResponse({"id": session.id})
    
def payment_success(request):
    session_id = request.GET.get("session_id")
    if not session_id:
        return render(request, "payment_failed.html", {"error": "Invalid session ID."})

    # Retrieve session details from Stripe
    session = stripe.checkout.Session.retrieve(session_id)

    # Ensure session exists
    if not session or session.payment_status != "paid":
        return render(request, "payment_failed.html", {"error": "Payment not successful."})

    invoice_id = session.metadata.get("invoice_id")  # Assuming metadata is set in checkout session
    invoice = get_object_or_404(Invoice, id=invoice_id)

    # Fetch invoice products
    invoice_products = InvoiceProduct.objects.filter(invoice=invoice)

    # Prepare product data for storage
    products_list = [
        {
            "name": item.product.name,
            "price": float(item.product.price),
            "quantity": item.quantity,
            "total_price": float(item.total_price),
        }
        for item in invoice_products
    ]

    total_amount = invoice_products.aggregate(Sum("total_price"))["total_price__sum"] or 0
    # Save transaction details
    transaction = Transaction(
        invoice=invoice,
        customer_name=invoice.customer_name,
        customer_number=invoice.customer_number,
        total_amount=total_amount,
        stripe_session_id=session.id,
    )
    transaction.set_products(products_list)
    transaction.save()

    return render(request, "payment_success.html", {"transaction": transaction})

def payment_cancel(request):
    return render(request, "payment_cancel.html")
    
def transactions_list(request):
    """View to display and filter transactions by date."""
    transactions = Transaction.objects.all()

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            transactions = transactions.filter(
                created_at__date__gte=start_date, created_at__date__lte=end_date
            )
        except ValueError:
            pass  # Handle invalid date format gracefully

    return render(request, "transactions.html", {"transactions": transactions})
    
def download_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    invoice_products = InvoiceProduct.objects.filter(invoice=invoice)
    total_price = sum(item.total_price for item in invoice_products)

    html_string = render_to_string('invoice_pdf.html', {
        'invoice': invoice,
        'invoice_products': invoice_products,
        'total_price': total_price,
    })

    html = HTML(string=html_string)
    result = html.write_pdf()

    response = HttpResponse(result, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=invoice_{invoice.id}.pdf'
    return response