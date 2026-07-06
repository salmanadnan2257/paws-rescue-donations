from django import forms
from .models import Donation


class DonationForm(forms.ModelForm):
    """Form for creating and editing donations."""
    
    donation_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        }),
        required=False,
        help_text='Leave empty to use current date/time'
    )
    
    class Meta:
        model = Donation
        fields = [
            'donor_name', 'donor_phone', 'donor_email',
            'pet_name', 'amount', 'currency',
            'payment_method', 'reference_no',
            'donation_date', 'notes'
        ]
        widgets = {
            'donor_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Donor Name'}),
            'donor_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+92 XXX XXXXXXX'}),
            'donor_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'donor@example.com'}),
            'pet_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pet Name'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'currency': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PKR'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'reference_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Reference/Transaction Number'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes...'}),
        }
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount < 0:
            raise forms.ValidationError('Amount must be greater than or equal to 0.')
        return amount
    
    def clean_donation_date(self):
        """Set donation_date to now if it's empty."""
        donation_date = self.cleaned_data.get('donation_date')
        if not donation_date:
            from django.utils import timezone
            donation_date = timezone.now()
        return donation_date


class DonationFilterForm(forms.Form):
    """Form for filtering and searching donations."""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by donor or pet name...'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='From Date'
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='To Date'
    )
    
    payment_method = forms.ChoiceField(
        required=False,
        choices=[('', 'All')] + Donation.PAYMENT_METHOD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Payment Method'
    )
    
    currency = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., PKR, USD'
        })
    )
    
    amount_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Lowest amount'
        }),
        label='Amount From'
    )
    
    amount_max = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Highest amount'
        }),
        label='Amount To'
    )
    
    sort_by = forms.ChoiceField(
        required=False,
        choices=[
            ('-donation_date', 'Date (Newest)'),
            ('donation_date', 'Date (Oldest)'),
            ('-amount', 'Amount (High to Low)'),
            ('amount', 'Amount (Low to High)'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='-donation_date'
    )
