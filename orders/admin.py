from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """Inline admin interface for OrderItem model."""
    model = OrderItem
    extra = 0
    raw_id_fields = ('item',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin interface configuration for the Order model."""
    list_display = ('id', 'status', 'total_amount', 'created_at', 'is_paid_display')
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'customer_email', 'stripe_session_id')
    readonly_fields = ('total_amount', 'created_at', 'updated_at', 'stripe_session_id', 'stripe_payment_intent_id')
    inlines = [OrderItemInline]

    def is_paid_display(self, obj: Order) -> bool:
        return obj.is_paid
    is_paid_display.boolean = True
    is_paid_display.short_description = 'Paid'

    fieldsets = (
        ('Order Information', {
            'fields': ('status', 'customer_email', 'total_amount')
        }),
        ('Items & Discounts', {
            'fields': ('discount', 'tax')
        }),
        ('Stripe Details', {
            'fields': ('stripe_session_id', 'stripe_payment_intent_id'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
