from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone


class Donation(models.Model):
    """Model representing a donation to the rescue organization."""
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('online', 'Online Payment'),
        ('other', 'Other'),
    ]
    
    # Donor information
    donor_name = models.CharField(max_length=255)
    donor_phone = models.CharField(max_length=50, blank=True, null=True)
    donor_email = models.EmailField(blank=True, null=True)
    
    # Donation details
    pet_name = models.CharField(max_length=255, help_text='Name of the pet this donation is for')
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    currency = models.CharField(max_length=10, default='PKR')
    
    # Payment information
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    reference_no = models.CharField(max_length=255, blank=True, null=True)
    
    # Additional information
    donation_date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'donations'
        ordering = ['-donation_date']
        verbose_name = 'Donation'
        verbose_name_plural = 'Donations'
    
    def __str__(self):
        return f'{self.donor_name} - {self.amount} {self.currency} for {self.pet_name}'
