from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.urls import reverse
from django.views.decorators.http import require_POST
from .models import Order, OrderItem
from products.models import Item
from taxes.models import Discount


def order_detail(request: HttpRequest, order_id: int) -> HttpResponse:
    order = get_object_or_404(Order, id=order_id)
    currency = order.get_currency()
    currency_lower = currency.lower()
    stripe_public_key = settings.STRIPE_KEYS.get(currency_lower, {}).get('public')
    
    return render(request, 'orders/order_detail.html', {
        'order': order,
        'stripe_public_key': stripe_public_key
    })


@require_POST
def create_order(request: HttpRequest, item_id: int) -> HttpResponseRedirect:
    """Adds an item to the current pending order or creates a new one"""
    item = get_object_or_404(Item, id=item_id)
    
    order_id = request.session.get('order_id')
    order = None
    
    if order_id:
        order = Order.objects.filter(id=order_id, status=Order.Status.PENDING).first()
        
    if not order:
        order = Order.objects.create(status=Order.Status.PENDING)
        request.session['order_id'] = order.id
    
    if order.items.exists():
        if order.items.first().currency != item.currency:
            from django.contrib import messages
            messages.warning(
                request,
                f"Started a new order because {item.name} uses a different currency ({item.currency}). Your previous order is saved but separate."
            )
            
            order = Order.objects.create(status=Order.Status.PENDING)
            request.session['order_id'] = order.id
            
    order_item, created = OrderItem.objects.get_or_create(
        order=order,
        item=item,
        defaults={'price': item.price}
    )
    
    if not created:
        order_item.quantity += 1
        order_item.save()
    
    order.save()
    
    return redirect('order_detail', order_id=order.id)


@require_POST
def apply_discount(request: HttpRequest, order_id: int) -> HttpResponseRedirect:
    """Applies a discount to an order by name"""
    order = get_object_or_404(Order, id=order_id)
    code = request.POST.get('discount_code')
    
    if code:
        try:
            discount = Discount.objects.get(name=code)
            order.discount = discount
            order.save()
        except Discount.DoesNotExist:
            pass
            
    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('order_detail', order_id=order.id)


def clear_new_order(request: HttpRequest) -> HttpResponseRedirect:
    """Clears the current session order_id to start a fresh order"""
    if 'order_id' in request.session:
        del request.session['order_id']
    return redirect('/')
