from django.db import models
from django.core.validators import MinValueValidator
from products.models import Item
from taxes.models import Discount, Tax


class Order(models.Model):
    """Order - combines several products"""

    class Status(models.TextChoices):
        """Defines possible order statuses."""
        PENDING = 'pending', 'Pending Payment'
        PROCESSING = 'processing', 'Processing'
        PAID = 'paid', 'Paid'
        CANCELLED = 'cancelled', 'Cancelled'
        REFUNDED = 'refunded', 'Refunded'

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Order Status'
    )

    items = models.ManyToManyField(
        Item,
        through='OrderItem',
        related_name='orders',
        verbose_name='Items'
    )

    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='Total Amount',
        help_text='Total order amount'
    )

    discount = models.ForeignKey(
        'taxes.Discount',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='Discount Applied'
    )

    tax = models.ForeignKey(
        'taxes.Tax',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='Tax Applied'
    )

    stripe_session_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Stripe Session ID'
    )

    stripe_payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Stripe Payment Intent ID'
    )

    customer_email = models.EmailField(
        blank=True,
        verbose_name='Customer Email'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['stripe_session_id']),
        ]

    def __str__(self) -> str:
        return f"Order #{self.id} - {self.get_status_display()} - ${self.total_amount}"

    def save(self, *args, **kwargs) -> None:
        """Recalculate total amount before saving"""
        if self.pk:
            self.total_amount = self.calculate_total()
        super().save(*args, **kwargs)

    def calculate_subtotal(self) -> float:
        subtotal = 0
        for order_item in self.order_items.all():
            subtotal += order_item.price * order_item.quantity
        return subtotal

    def calculate_discount_amount(self) -> float:
        if not self.discount:
            return 0

        subtotal = self.calculate_subtotal()

        if self.discount.discount_type == Discount.DiscountType.PERCENTAGE:
            return subtotal * (self.discount.amount / 100)
        else:
            return self.discount.amount

    def calculate_tax_amount(self) -> float:
        if not self.tax:
            return 0

        subtotal = self.calculate_subtotal()
        discount_amount = self.calculate_discount_amount()
        taxable_amount = subtotal - discount_amount

        return taxable_amount * (self.tax.rate / 100)

    def calculate_total(self) -> float:
        subtotal = self.calculate_subtotal()
        discount_amount = self.calculate_discount_amount()
        tax_amount = self.calculate_tax_amount()

        return max(0, subtotal - discount_amount + tax_amount)

    def get_currency(self) -> str:
        """Get currency of the first item"""
        if self.items.exists():
            return self.items.first().currency
        return 'USD'

    @property
    def is_paid(self) -> bool:
        return self.status == self.Status.PAID

    @property
    def currency_symbol(self) -> str:
        currency = self.get_currency()
        symbols = {'USD': '$', 'EUR': '€'}
        return symbols.get(currency, currency)

    @property
    def formatted_total(self) -> str:
        """Get the formatted total amount with currency symbol"""
        return f"{self.currency_symbol}{self.total_amount:.2f}"


class OrderItem(models.Model):
    """An intermediate model for associating an Order-Item"""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='order_items'
    )

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='order_items'
    )

    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Quantity'
    )

    price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Price at Order'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        unique_together = ['order', 'item']

    def __str__(self) -> str:
        return f"{self.item.name} x{self.quantity} in Order #{self.order.id}"

    def save(self, *args, **kwargs) -> None:
        """Save the item price at the time of adding to the order"""
        if not self.price:
            self.price = self.item.price
        super().save(*args, **kwargs)

    @property
    def subtotal(self) -> float:
        return self.price * self.quantity
