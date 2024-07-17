from django.urls import path
from .views import AbandonedCheckoutView, OrderConfirmationView

urlpatterns = [
    path('abandoned_checkout/', AbandonedCheckoutView.as_view(), name='abandoned_checkout'),
    path('order_confirmation/', OrderConfirmationView.as_view(), name='order_confirmation'),
    # Add other URLs as needed
]