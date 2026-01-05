from django.contrib import admin
from .models import Discount, Tax


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount', 'discount_type', 'stripe_coupon_id')
    list_filter = ('discount_type',)
    search_fields = ('name', 'stripe_coupon_id')


@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    list_display = ('name', 'rate', 'stripe_tax_rate_id')
    search_fields = ('name', 'stripe_tax_rate_id')

