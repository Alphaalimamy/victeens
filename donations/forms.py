from django import forms
from django.core.validators import MinValueValidator
from .models import Donation, DonationCampaign
import json

class DonationForm(forms.ModelForm):
    AMOUNT_CHOICES = [
        (500, 'Le 500 - Feed a teen for a day'),
        (1000, 'Le 1,000 - School supplies for a week'),
        (5000, 'Le 5,000 - Medical care for a month'),
        (10000, 'Le 10,000 - Vocational training materials'),
        (25000, 'Le 25,000 - One month of shelter'),
        ('custom', 'Custom Amount'),
    ]
    
    DONATION_TYPES = [
        ('one_time', 'One-time Donation'),
        ('monthly', 'Monthly - Ongoing support'),
        ('quarterly', 'Quarterly - Regular impact'),
        ('yearly', 'Yearly - Annual commitment'),
    ]
    
    PAYMENT_METHODS = [
        ('mpesa', 'M-Pesa - Mobile Money'),
        ('stripe', 'Credit/Debit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    preset_amount = forms.ChoiceField(
        choices=AMOUNT_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'hidden'}),
        initial=1000
    )
    
    custom_amount = forms.DecimalField(
        required=False,
        min_value=1,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'input-field',
            'placeholder': 'Enter amount in KES',
            'min': '1',
            'step': '1'
        })
    )
    
    donation_type = forms.ChoiceField(
        choices=DONATION_TYPES,
        widget=forms.RadioSelect(attrs={'class': 'hidden'}),
        initial='one_time'
    )
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHODS,
        widget=forms.RadioSelect(attrs={'class': 'hidden'}),
        initial='mpesa'
    )
    
    is_anonymous = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-vto-orange-dark rounded'})
    )
    
    is_dedicated = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-vto-orange-dark rounded'})
    )
    
    dedication_name = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': 'Name of person you\'re dedicating to'
        })
    )
    
    dedication_message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'input-field',
            'rows': 3,
            'placeholder': 'Optional dedication message'
        })
    )
    
    # Guest donor fields
    guest_donor = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-vto-orange-dark rounded'})
    )
    
    donor_name = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': 'Your full name'
        })
    )
    
    donor_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'input-field',
            'placeholder': 'your@email.com'
        })
    )
    
    donor_phone = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': '+23277000000'
        })
    )
    
    agree_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-vto-orange-dark rounded'})
    )
    
    class Meta:
        model = Donation
        fields = ['amount', 'donation_type', 'campaign', 'payment_method']
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Set initial values for authenticated users
        if self.request and self.request.user.is_authenticated:
            user = self.request.user
            self.fields['donor_name'].initial = user.get_full_name()
            self.fields['donor_email'].initial = user.email
            self.fields['donor_phone'].initial = user.phone
        
        # Add campaign choices
        active_campaigns = DonationCampaign.objects.filter(is_active=True)
        self.fields['campaign'] = forms.ModelChoiceField(
            queryset=active_campaigns,
            required=False,
            empty_label="General Fund (Most Needed)",
            widget=forms.Select(attrs={'class': 'input-field'})
        )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Determine the final amount
        preset_amount = cleaned_data.get('preset_amount')
        custom_amount = cleaned_data.get('custom_amount')
        
        if preset_amount == 'custom':
            if not custom_amount:
                self.add_error('custom_amount', 'Please enter a custom amount')
            else:
                cleaned_data['amount'] = custom_amount
        else:
            cleaned_data['amount'] = preset_amount
        
        # Validate guest donor fields
        guest_donor = cleaned_data.get('guest_donor')
        if guest_donor:
            if not cleaned_data.get('donor_name'):
                self.add_error('donor_name', 'Name is required for guest donations')
            if not cleaned_data.get('donor_email'):
                self.add_error('donor_email', 'Email is required for guest donations')
        else:
            # For authenticated users, use their info
            if self.request and self.request.user.is_authenticated:
                cleaned_data['guest_donor'] = False
        
        # Validate dedication
        is_dedicated = cleaned_data.get('is_dedicated')
        dedication_name = cleaned_data.get('dedication_name')
        
        if is_dedicated and not dedication_name:
            self.add_error('dedication_name', 'Please provide a name for the dedication')
        
        return cleaned_data


class MpesaPaymentForm(forms.Form):
    """Form for M-Pesa payment details"""
    phone_number = forms.CharField(
        max_length=13,
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': '0722 123 456',
            'pattern': '^0[17]\d{8}$'
        })
    )
    
    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']
        # Clean the phone number
        phone = phone.replace(' ', '').replace('-', '').replace('+', '')
        
        # Convert to 254 format if it starts with 0
        if phone.startswith('0'):
            phone = '232' + phone[1:]
        
        # Validate Kenyan mobile number
        if not phone.startswith('232') or len(phone) != 12:
            raise forms.ValidationError('Please enter a valid Kenyan mobile number (e.g., 232 77 123 456)')
        
        return phone


class CardPaymentForm(forms.Form):
    """Form for card payment details (Stripe)"""
    card_number = forms.CharField(
        max_length=19,
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': '1234 5678 9012 3456',
            'data-stripe': 'number'
        })
    )
    
    card_expiry = forms.CharField(
        max_length=7,
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': 'MM/YY',
            'data-stripe': 'exp'
        })
    )
    
    card_cvc = forms.CharField(
        max_length=4,
        widget=forms.PasswordInput(attrs={
            'class': 'input-field',
            'placeholder': 'CVC',
            'data-stripe': 'cvc'
        })
    )
    
    card_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': 'Name on card'
        })
    )
    
    save_card = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-vto-orange-dark rounded'})
    )


class BankTransferForm(forms.Form):
    """Form for bank transfer information"""
    reference_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': 'Your payment reference'
        })
    )
    
    transfer_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'input-field',
            'type': 'date'
        })
    )
    
    receipt_upload = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'input-field',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )