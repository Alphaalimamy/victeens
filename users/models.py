from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator

class User(AbstractUser):
    """Custom User model with extended fields"""
    ROLE_CHOICES = [
        ('donor', 'Donor'),
        ('volunteer', 'Volunteer'),
        ('staff', 'Staff Member'),
        ('admin', 'Administrator'),
    ]
    
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='donor')
    phone = models.CharField(max_length=20, blank=True, validators=[
        RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    ])
    
    # Profile Information
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Address
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Communication Preferences
    newsletter_subscription = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    # Donor Specific
    is_anonymous_donor = models.BooleanField(default=False)
    
    # Volunteer Specific
    skills = models.TextField(blank=True)
    availability = models.CharField(max_length=100, blank=True)
    
    # Metadata
    email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    last_login_user_agent = models.TextField(blank=True)
    
    # GDPR Compliance
    data_processing_consent = models.BooleanField(default=False)
    consent_date = models.DateTimeField(null=True, blank=True)
    marketing_consent = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.get_full_name() or self.email} ({self.get_role_display()})"
    
    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)
    
    def get_initials(self):
        """Get user initials for avatar"""
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        elif self.first_name:
            return self.first_name[0].upper()
        elif self.username:
            return self.username[0].upper()
        return "U"
    
    @property
    def is_staff_member(self):
        return self.role in ['staff', 'admin']
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_volunteer(self):
        return self.role == 'volunteer'
    
    @property
    def is_donor(self):
        return self.role == 'donor'