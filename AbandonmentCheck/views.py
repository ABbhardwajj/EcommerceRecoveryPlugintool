from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from .models import CheckoutStatus, EcommercePlatform, Scheduler
from .tasks import send_recovery_message, update_with_order, revoke_scheduled_recovery_tasks, schedule_recovery_messages



class AbandonedCheckoutView(APIView):
    def post(self, request):
        # import ipdb;
        # ipdb.set_trace()
        data = request.data

        # Extract data from the request
        checkout_id = data.get('checkout_id')
        customer_email = data.get('customer_email')
        cart_id = data.get('cart_id')
        user_id = data.get('user_id')
        ecommerce_platform_id = data.get('platform_id')
        abandoned_checkout_url = data.get('abandoned_checkout_url')

        # Validate data
        if not all([checkout_id, customer_email, cart_id, user_id, ecommerce_platform_id]):
            return Response({"error": "Incomplete data"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Check if there's an existing checkout status with the same cart_id, user_id, and ecommerce_platform_id
            existing_checkout_status = CheckoutStatus.objects.filter(
                cart_id=cart_id,
                user_id=user_id,
                ecommerce_platform_id=ecommerce_platform_id
            ).first()

            if existing_checkout_status:
                # Revoke old scheduled tasks and delete Scheduler entries
                revoke_scheduled_recovery_tasks(existing_checkout_status.id)
                Scheduler.objects.filter(checkout_status=existing_checkout_status).delete()

                # Update existing checkout status
                existing_checkout_status.customer_email = customer_email
                existing_checkout_status.abandoned_checkout_url = abandoned_checkout_url
                existing_checkout_status.is_abandoned = True
                existing_checkout_status.created_at = timezone.now()
                existing_checkout_status.save()

                # Schedule recovery messages
                schedule_recovery_messages.apply_async(args=[existing_checkout_status.id])

                return Response({"message": "Updated existing abandoned checkout", "checkout_id": existing_checkout_status.checkout_id}, status=status.HTTP_200_OK)
            else:
                # Create new checkout status
                checkout_status = CheckoutStatus.objects.create(
                    checkout_id=checkout_id,
                    customer_email=customer_email,
                    cart_id=cart_id,
                    user_id=user_id,
                    ecommerce_platform_id=ecommerce_platform_id,
                    abandoned_checkout_url=abandoned_checkout_url,
                    is_abandoned=True,
                    created_at=timezone.now()
                )

                # Schedule recovery messages for the new checkout
                # schedule_recovery_messages(checkout_status.id)
                schedule_recovery_messages.apply_async(args=[checkout_status.id])

                return Response({"message": "New abandoned checkout created", "checkout_id": checkout_status.checkout_id}, status=status.HTTP_201_CREATED)

        except EcommercePlatform.DoesNotExist:
            return Response({"error": "Ecommerce platform not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class OrderConfirmationView(APIView):
    def post(self, request):
        data = request.data

        # Extract data from the request
        order_id = data.get('order_id')
        checkout_id = data.get('checkout_id')
        ecommerce_platform_id = data.get('platform_id')
        user_id = data.get('user_id')

        # Validate data
        if not all([order_id, checkout_id, ecommerce_platform_id, user_id]):
            return Response({"error": "Incomplete data"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Update checkout status when order is confirmed
            checkout_status = CheckoutStatus.objects.get(checkout_id=checkout_id, user_id = user_id, ecommerce_platform_id = ecommerce_platform_id)
            checkout_status.update_with_order(order_id)

            # Cancel scheduled recovery messages
            revoke_scheduled_recovery_tasks(checkout_status.id)
            Scheduler.objects.filter(checkout_status_id=checkout_status.id).delete()

            return Response({"message": "Order confirmation received", "order_id": order_id}, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response({"error": "Checkout not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
