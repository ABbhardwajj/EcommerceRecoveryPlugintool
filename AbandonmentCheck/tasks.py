import os
from django.conf import settings
from celery import shared_task
from django.core.mail import send_mail
from datetime import timedelta
from django.utils import timezone
from .models import CheckoutStatus, Scheduler
from celery import current_app



@shared_task
def send_recovery_message(checkout_id, customer_email, eta):
    
    try :
        scheduler_entry = Scheduler.objects.filter(checkout_status_id=checkout_id, is_sent=False, eta=eta).first()
        subject = 'Complete Your Purchase'
        message = 'You left items in your cart. Click here to complete your purchase.'
        from_email = settings.MAIL_SENDING_USER
        to_email = [customer_email]
        send_mail(subject, message, from_email, to_email)
        scheduler_entry.is_sent = True
        scheduler_entry.message = message
        scheduler_entry.save()

    except Scheduler.DoesNotExist:
        print(f"Scheduler entry for checkout ID {checkout_id} not found or already sent.")
    except Exception as e:
        print(f"Error sending recovery message: {e}")

@shared_task
def schedule_recovery_messages(checkout_id):
    try:
        
        print(f"Task started for scheduling recovery messages for checkout ID {checkout_id}")
        checkout_status = CheckoutStatus.objects.get(pk=checkout_id)
        print(f"Retrieved checkout status: {checkout_status}")
        

        intervals_str = checkout_status.ecommerce_platform.email_intervals
        intervals = [int(interval.strip().strip('"')) for interval in intervals_str.split(',')]

        
        print(f"Intervals for sending emails: {intervals}")
        

        if checkout_status.is_abandoned and intervals:
            for interval in intervals:
                interval =2
                eta = checkout_status.created_at + timedelta(minutes=int(interval))
                message = f"Recovery message for checkout ID {checkout_status.checkout_id} at {eta}"
                
                # Create Scheduler entry
                Scheduler.objects.create(
                    checkout_status=checkout_status,
                    email_interval=interval,
                    eta=eta,
                    is_sent=False,  # Assuming it's not sent initially
                    user_id=checkout_status.user_id,
                    ecommerce_platform=checkout_status.ecommerce_platform,
                    message=message
                )

                # Schedule Celery task
                # send_recovery_message(checkout_status.id, checkout_status.customer_email, eta=eta)
                send_recovery_message.apply_async(args=[checkout_status.id, checkout_status.customer_email,eta])
                

    except CheckoutStatus.DoesNotExist:
        print(f"CheckoutStatus with ID {checkout_id} does not exist.")

@shared_task
def revoke_scheduled_recovery_tasks(checkout_status_id):
    try:
        # Query Celery's scheduled tasks
        app = current_app
        scheduler = app.control.inspect().scheduled()
        
        if scheduler:
            # Iterate through scheduled tasks
            for worker, tasks in scheduler.items():
                for task in tasks:
                    # Check if task matches our criteria (e.g., based on checkout_status_id)
                    if task['request']['args'] and str(checkout_status_id) in task['request']['args']:
                        # Revoke the task
                        app.control.revoke(task['request']['id'], terminate=True)
                        print(f"Revoked task {task['request']['id']} for checkout_status_id {checkout_status_id}")
    except Exception as e:
        print(f"Error revoking tasks: {e}")


@shared_task
def update_with_order(order_id, checkout_id):
    try:
        checkout_status = CheckoutStatus.objects.get(checkout_id=checkout_id)
        checkout_status.is_abandoned = False
        checkout_status.order_id = order_id
        checkout_status.save()

        # Cancel scheduled recovery messages
        revoke_scheduled_recovery_tasks(checkout_status.id)
        Scheduler.objects.filter(checkout_status_id=checkout_status.id).delete()
    except CheckoutStatus.DoesNotExist:
        print(f"CheckoutStatus with checkout_id={checkout_id} does not exist")
    except Exception as e:
        print(f"Error updating checkout status: {e}")
