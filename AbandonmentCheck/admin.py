from django.contrib import admin
from .models import CheckoutStatus, EcommercePlatform, Scheduler
admin.site.register(CheckoutStatus)
admin.site.register(EcommercePlatform)
admin.site.register(Scheduler)

