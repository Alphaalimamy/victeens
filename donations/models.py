from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.crypto import get_random_string


class DonationCategory(models.Model):
    """Categories for different types of donations"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, help_text="Font Awesome class")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        verbose_name_plural = "Donation Categories"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class DonationCampaign(models.Model):
    """Fundraising campaigns"""
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    goal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='campaigns/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_featured', '-start_date']
    
    def __str__(self):
        return self.title
    
    @property
    def progress_percentage(self):
        if self.goal_amount == 0:
            return 0
        return min(100, (self.current_amount / self.goal_amount) * 100)
    
    @property
    def days_left(self):
        if self.end_date:
            delta = self.end_date - timezone.now().date()
            return max(0, delta.days)
        return None
    
    @property
    def is_ongoing(self):
        if self.end_date:
            return self.start_date <= timezone.now().date() <= self.end_date
        return self.start_date <= timezone.now().date()


class Donation(models.Model):
    """Main donation model"""
    DONATION_TYPES = [
        ('one_time', 'One-time Donation'),
        ('monthly', 'Monthly Recurring'),
        ('quarterly', 'Quarterly Recurring'),
        ('yearly', 'Yearly Recurring'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHODS = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('mpesa', 'M-Pesa'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
    ]
    
    # Donation Information
    donation_id = models.CharField(max_length=20, unique=True, editable=False)
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                             null=True, blank=True, related_name='donations')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    donation_type = models.CharField(max_length=20, choices=DONATION_TYPES, default='one_time')
    category = models.ForeignKey(DonationCategory, on_delete=models.SET_NULL, null=True, blank=True)
    campaign = models.ForeignKey(DonationCampaign, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Donor Information (can be different from user account for guest donations)
    guest_donor = models.BooleanField(default=False)
    donor_name = models.CharField(max_length=200, blank=True)
    donor_email = models.EmailField(blank=True)
    donor_phone = models.CharField(max_length=20, blank=True)
    is_anonymous = models.BooleanField(default=False)
    is_dedicated = models.BooleanField(default=False)
    dedication_name = models.CharField(max_length=200, blank=True)
    dedication_message = models.TextField(blank=True)
    
    # Payment Information
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=100, blank=True)
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    currency = models.CharField(max_length=3, default='USD')
    
    # Recurring Donation Information
    is_recurring = models.BooleanField(default=False)
    recurring_id = models.CharField(max_length=100, blank=True)  # ID from payment processor
    next_payment_date = models.DateField(null=True, blank=True)
    recurring_end_date = models.DateField(null=True, blank=True)
    
    # Administrative
    notes = models.TextField(blank=True)
    receipt_sent = models.BooleanField(default=False)
    receipt_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['donation_id']),
            models.Index(fields=['donor', 'created_at']),
            models.Index(fields=['payment_status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Donation {self.donation_id} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        if not self.donation_id:
            # Generate unique donation ID: VTO-YYYYMMDD-RANDOM
            date_str = timezone.now().strftime('%Y%m%d')
            random_str = get_random_string(6, '0123456789')
            self.donation_id = f"VTO-{date_str}-{random_str}"
        
        # Set donor information if guest donation
        if self.donor and not self.guest_donor:
            self.donor_name = self.donor.get_full_name() or self.donor.email
            self.donor_email = self.donor.email
            self.donor_phone = self.donor.phone
        
        super().save(*args, **kwargs)
    
    def get_donor_display_name(self):
        """Get display name for donor (respects anonymity)"""
        if self.is_anonymous:
            return "Anonymous Donor"
        return self.donor_name or "Guest Donor"
    
    @property
    def is_successful(self):
        return self.payment_status == 'completed'
    
    @property
    def receipt_number(self):
        return f"VTO-RCPT-{self.created_at.strftime('%Y%m')}-{self.id:06d}"


class RecurringDonation(models.Model):
    """Track recurring donation subscriptions"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recurring_donations')
    donation = models.OneToOneField(Donation, on_delete=models.CASCADE, related_name='recurring_subscription')
    subscription_id = models.CharField(max_length=100, unique=True)  # From payment processor
    frequency = models.CharField(max_length=20, choices=Donation.DONATION_TYPES[1:])  # Exclude one_time
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField()
    next_payment_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    total_payments = models.IntegerField(default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Payment method details
    payment_method = models.CharField(max_length=20, choices=Donation.PAYMENT_METHODS)
    payment_method_last4 = models.CharField(max_length=4, blank=True)  # Last 4 digits of card/bank
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Recurring Donation {self.subscription_id} - {self.donor.email}"


class DonationReceipt(models.Model):
    """Generated receipts for donations"""
    donation = models.OneToOneField(Donation, on_delete=models.CASCADE, related_name='receipt')
    receipt_number = models.CharField(max_length=50, unique=True)
    pdf_file = models.FileField(upload_to='receipts/', null=True, blank=True)
    html_content = models.TextField(blank=True)  # Store HTML receipt for email
    sent_via_email = models.BooleanField(default=False)
    sent_via_sms = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Receipt {self.receipt_number}"


class ImpactReport(models.Model):
    """How donations are making an impact"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    donation_range_min = models.DecimalField(max_digits=10, decimal_places=2, help_text="Minimum donation amount for this impact")
    donation_range_max = models.DecimalField(max_digits=10, decimal_places=2, help_text="Maximum donation amount for this impact")
    image = models.ImageField(upload_to='impact-reports/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['donation_range_min']
    
    def __str__(self):
        return self.title
    
    @property
    def impact_range(self):
        return f"USD {self.donation_range_min:,.0f} - USD {self.donation_range_max:,.0f}"