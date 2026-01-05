import stripe
from django.conf import settings
from django.http import JsonResponse, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from products.models import Item
from orders.models import Order, OrderItem


def get_stripe_client(currency: str):
    """Returns a configured stripe module based on currency"""
    currency_lower = currency.lower()
    keys = settings.STRIPE_KEYS.get(currency_lower)
    if not keys:
        raise ValueError(f"No stripe keys configured for currency: {currency}")
    stripe.api_key = keys['secret']
    return stripe


def create_order_checkout_session(request: HttpRequest, order_id: int) -> JsonResponse:
    """Create a Stripe Checkout Session for an entire order (Bonus)"""
    order = get_object_or_404(Order, id=order_id)
    currency = order.get_currency()
    
    try:
        stripe_client = get_stripe_client(currency)
        
        line_items = []
        for order_item in order.order_items.all():
            item_data = {
                'price_data': {
                    'currency': currency.lower(),
                    'product_data': {
                        'name': order_item.item.name,
                    },
                    'unit_amount': int(order_item.price * 100),
                },
                'quantity': order_item.quantity,
            }
            
            # Add tax rates if applicable
            if order.tax and order.tax.stripe_tax_rate_id:
               item_data['tax_rates'] = [order.tax.stripe_tax_rate_id]
               
            line_items.append(item_data)

        discounts = []
        if order.discount:
            if order.discount.stripe_coupon_id:
                discounts.append({'coupon': order.discount.stripe_coupon_id})

        base_url = request.build_absolute_uri('/')[:-1]
        success_url = f"{base_url}/success/?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{base_url}{reverse('order_detail', args=[order.id])}?cancelled=true"

        checkout_params = {
            'payment_method_types': ['card'],
            'line_items': line_items,
            'mode': 'payment',
            'success_url': success_url,
            'cancel_url': cancel_url,
        }

        if discounts:
            checkout_params['discounts'] = discounts

        session = stripe_client.checkout.Session.create(**checkout_params)
        
        # Save session ID to order
        order.stripe_session_id = session.id
        order.save()
        
        return JsonResponse({'id': session.id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def create_order_payment_intent(request: HttpRequest, order_id: int) -> JsonResponse:
    """Create a Stripe Payment Intent for an Order"""
    order = get_object_or_404(Order, id=order_id)
    currency = order.get_currency()
    
    try:
        stripe_client = get_stripe_client(currency)
        
        # Calculate amount including tax and discount
        amount = int(order.calculate_total() * 100)
        
        if amount < 1:
             return JsonResponse({'error': 'Order amount must be at least 0.01'}, status=400)
        
        intent = stripe_client.PaymentIntent.create(
            amount=amount,
            currency=currency.lower(),
            metadata={'order_id': order.id}
        )
        
        # Save intent ID to order
        order.stripe_payment_intent_id = intent.id
        order.save()
        
        return JsonResponse({'clientSecret': intent.client_secret})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def create_order_direct(request: HttpRequest, item_id: int) -> HttpResponseRedirect:
    """Create an Order and redirect to the Payment Intent checkout page (Direct Payment)"""
    item = get_object_or_404(Item, id=item_id)
    
    order = Order.objects.create(status=Order.Status.PENDING)
    OrderItem.objects.create(order=order, item=item, quantity=1, price=item.price)
    order.save()

    return redirect('order_payment', order_id=order.id)


def order_payment(request: HttpRequest, order_id: int) -> HttpResponse:
    """Render the Payment Intent checkout page for an Order"""
    order = get_object_or_404(Order, id=order_id)
    currency_lower = order.get_currency().lower()
    stripe_public_key = settings.STRIPE_KEYS.get(currency_lower, {}).get('public')
    
    return_url = request.build_absolute_uri('/success/')

    return render(request, 'payments/payment_intent.html', {
        'order': order,
        'item': order.order_items.first().item,
        'stripe_public_key': stripe_public_key,
        'return_url': return_url
    })


def payment_success(request: HttpRequest) -> HttpResponse:
    """
    Handles payment success.
    Verifies the Payment Intent status with Stripe and updates the Order.
    """
    payment_intent_id = request.GET.get('payment_intent')
    client_secret = request.GET.get('payment_intent_client_secret')
    
    session_id = request.GET.get('session_id')
    if session_id:
        order = Order.objects.filter(stripe_session_id=session_id).first()
        if order:
            stripe_client = get_stripe_client(order.get_currency())
            session = stripe_client.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                order.status = Order.Status.PAID
                order.save()
                
                # Clear session order_id if it matches, so user starts fresh
                if str(request.session.get('order_id')) == str(order.id):
                    del request.session['order_id']


    if payment_intent_id and client_secret:
        order = Order.objects.filter(stripe_payment_intent_id=payment_intent_id).first()
        
        if order:
            stripe_client = get_stripe_client(order.get_currency())
            intent = stripe_client.PaymentIntent.retrieve(payment_intent_id)
            if intent.status == 'succeeded':
                order.status = Order.Status.PAID
                order.save()
                
                # Clear session order_id if it matches
                if str(request.session.get('order_id')) == str(order.id):
                    del request.session['order_id']

    return render(request, 'success.html')
