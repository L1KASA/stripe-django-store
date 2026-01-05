from django.contrib import admin
from .models import Item


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_display', 'currency', 'created_at')
    list_filter = ('currency', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Product Information', {
            'fields': ('name', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'currency'),
            'description': 'Price information for Stripe checkout'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def price_display(self, obj):
        symbols = {'USD': '$', 'EUR': '€'}
        symbol = symbols.get(obj.currency, obj.currency)
        return f"{symbol}{obj.price:.2f}"
