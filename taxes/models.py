from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Discount(models.Model):
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'percentage', 'Percentage'
        FIXED = 'fixed', 'Fixed Amount'

    name = models.CharField(max_length=100)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Amount or percentage of discount'
    )
    discount_type = models.CharField(
        max_length=10,
        choices=DiscountType.choices,
        default=DiscountType.PERCENTAGE
    )
    stripe_coupon_id = models.CharField(
        max_length=100,
        blank=True,
        help_text='Stripe Coupon ID (if already created in Stripe)'
    )

    def __str__(self) -> str:
        suffix = '%' if self.discount_type == self.DiscountType.PERCENTAGE else ''
        return f"{self.name} ({self.amount}{suffix})"


class Tax(models.Model):
    name = models.CharField(max_length=100)
    rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Tax rate in percentage'
    )
    stripe_tax_rate_id = models.CharField(
        max_length=100,
        blank=True,
        help_text='Stripe Tax Rate ID (if already created in Stripe)'
    )

    class Meta:
        verbose_name_plural = 'Taxes'

    def __str__(self) -> str:
        return f"{self.name} ({self.rate}%)"
