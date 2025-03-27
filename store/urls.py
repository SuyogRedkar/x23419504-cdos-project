from django.urls import path
from . import views

urlpatterns = [
    path('sign-up/',views.store_sign_up,name='store_sign_up'),
    path('login/',views.store_login,name='store_login'),
    path('logout/',views.store_logout,name='store_logout'),
    path('dashboard/',views.dashboard,name='dashboard'),
    path('product/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('product/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('addproduct/', views.add_product, name='add_product'),
    path('makebill/', views.makebill, name='makebill'),
    path('invoice/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path("create-checkout-session/<int:invoice_id>/", views.create_checkout_session, name="create_checkout_session"),
    path("payment-success/", views.payment_success, name="payment_success"),
    path("payment-cancel/", views.payment_cancel, name="payment_cancel"),
    path("transactions/", views.transactions_list, name="transactions"),
]