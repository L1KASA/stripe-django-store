from django.db import models


class Item(models.Model):
    class Currency(models.TextChoices):
        USD = 'USD', 'US Dollar'
        EUR = 'EUR', 'Euro'

    name = models.CharField(
        max_length=100,
        verbose_name='Item Name',
        help_text='Enter a name for the item',
    )
    description = models.TextField(
        verbose_name='Description',
        help_text='Enter a description for the item',
        blank=True,
    )
    price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Price',
        help_text='Enter a price for the item',
    )
    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.USD,
        verbose_name='Currency',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at',
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated at',
    )

    class Meta:
        verbose_name = 'Item'
        verbose_name_plural = 'Items'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['price']),
            models.Index(fields=['currency']),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.price} {self.currency})"
