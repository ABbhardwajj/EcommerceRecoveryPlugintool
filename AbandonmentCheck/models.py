from datetime import timezone
from django.db import models

class EcommercePlatform(models.Model):
    name = models.CharField(max_length=100)
    email_intervals = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class CheckoutStatus(models.Model):
    checkout_id = models.IntegerField(unique=True)
    customer_email = models.EmailField()
    cart_id = models.IntegerField()
    user_id = models.IntegerField()
    ecommerce_platform = models.ForeignKey(EcommercePlatform, on_delete=models.CASCADE, blank =True,null=True)
    abandoned_checkout_url = models.URLField(blank=True, null=True)
    is_abandoned = models.BooleanField(default=True)
    recovery_messages = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    order_id = models.IntegerField(blank=True, null=True)

    def update_with_order(self, order_id):
        self.is_abandoned = False
        self.order_id = order_id
        self.save()

    def add_recovery_message(self, message):
        
        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.recovery_messages:
            self.recovery_messages += f"\n{timestamp}: {message}"
        else:
            self.recovery_messages = f"{timestamp}: {message}"
        self.save()

    def __str__(self):
        return self.customer_email

class Scheduler(models.Model):
    checkout_status = models.ForeignKey(CheckoutStatus, on_delete=models.CASCADE)
    email_interval = models.CharField(max_length=255)  # Comma-separated intervals
    eta = models.DateTimeField()
    is_sent = models.BooleanField(default=False)
    user_id = models.IntegerField()
    ecommerce_platform = models.ForeignKey(EcommercePlatform, on_delete=models.CASCADE, blank =True,null=True)
    message = models.TextField()

    def __str__(self):
        return f'{self.ecommerce_platform.name}+" " {self.eta}'