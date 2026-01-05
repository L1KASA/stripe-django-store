from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from .models import Item


def item_list(request: HttpRequest) -> HttpResponse:
    items = Item.objects.all()
    return render(request, 'products/item_list.html', {'items': items})


def item_detail(request: HttpRequest, item_id) -> HttpResponse:
    item = get_object_or_404(Item, id=item_id)
    currency_lower = item.currency.lower()
    stripe_public_key = settings.STRIPE_KEYS.get(currency_lower, {}).get('public')
    
    symbols = {'USD': '$', 'EUR': '€'}
    symbol = symbols.get(item.currency, item.currency)
    item.formatted_price = f"{symbol}{item.price:.2f}"

    return render(request, 'products/item_detail.html', {
        'item': item,
        'stripe_public_key': stripe_public_key
    })
