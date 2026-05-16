from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from django.core.exceptions import ValidationError

from donations.models import Donation

class ChildCategory(models.Model):
    """Categories for children (age groups, needs, etc.)"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome class")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        verbose_name_plural = "Child Categories"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class Child(models.Model):
    """Main child model with privacy protection"""
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active - In our care'),
        ('graduated', 'Graduated - Successfully transitioned'),
        ('reunited', 'Reunited - With family'),
        ('transferred', 'Transferred - To another program'),
        ('deceased', 'Deceased'),
    ]
    
    # Identification (Privacy Protected)
    code_name = models.CharField(max_length=100, unique=True, help_text="Public display name for privacy")
    internal_id = models.CharField(max_length=20, unique=True, editable=False)  # For staff only
    slug = models.SlugField(unique=True, blank=True)
    
    # Basic Information (Minimal for public)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    age = models.IntegerField(validators=[MinValueValidator(13), MaxValueValidator(19)])
    date_of_birth = models.DateField(null=True, blank=True)  # Staff only
    place_of_birth = models.CharField(max_length=100, blank=True)  # Staff only
    
    # Current Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    date_admitted = models.DateField()
    date_departed = models.DateField(null=True, blank=True)
    
    # Background (General for public)
    background_summary = models.TextField(help_text="Public-friendly background (privacy protected)")
    private_background = models.TextField(blank=True, help_text="Full background (staff only)")
    
    # Needs & Interests
    current_needs = models.TextField(blank=True, help_text="Current needs for sponsorship")
    interests = models.TextField(blank=True, help_text="Hobbies, interests, talents")
    educational_level = models.CharField(max_length=100, blank=True)
    career_aspirations = models.TextField(blank=True)
    
    # Health Information (Staff only)
    health_status = models.TextField(blank=True, help_text="General health information (staff only)")
    special_needs = models.TextField(blank=True, help_text="Any special needs or disabilities")
    
    # Sponsorship
    is_sponsored = models.BooleanField(default=False)
    sponsorship_needed = models.BooleanField(default=True)
    sponsorship_amount = models.DecimalField(max_digits=10, decimal_places=2, default=10000.00, 
                                           help_text="Monthly sponsorship amount")
    
    # Categories
    categories = models.ManyToManyField(ChildCategory, blank=True)
    
    # Privacy & Consent
    photo_consent = models.BooleanField(default=False, help_text="Consent for photos")
    story_consent = models.BooleanField(default=False, help_text="Consent for sharing story")
    consent_date = models.DateField(null=True, blank=True)
    consent_expiry = models.DateField(null=True, blank=True)
    
    # Administrative
    case_manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                   null=True, blank=True, limit_choices_to={'role': 'staff'},
                                   related_name='managed_children')
    notes = models.TextField(blank=True, help_text="Staff notes")
    
    # Metadata
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False, help_text="Visible to public")
    display_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'code_name']
        verbose_name_plural = "Children"
        indexes = [
            models.Index(fields=['slug', 'is_published']),
            models.Index(fields=['status', 'is_published']),
        ]
    
    def __str__(self):
        return f"{self.code_name} ({self.age} years)"
    
    def save(self, *args, **kwargs):
        if not self.internal_id:
            # Generate unique internal ID: VTO-CHILD-YYYY-RANDOM
            year = timezone.now().strftime('%Y')
            random_str = get_random_string(6, '0123456789')
            self.internal_id = f"VTO-CHILD-{year}-{random_str}"
        
        if not self.slug:
            self.slug = slugify(self.code_name)
        
        # Ensure unique slug
        original_slug = self.slug
        counter = 1
        while Child.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            self.slug = f"{original_slug}-{counter}"
            counter += 1
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validate age and dates"""
        if self.date_of_birth:
            today = timezone.now().date()
            age = today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
            if age != self.age:
                raise ValidationError({
                    'age': f'Age ({self.age}) does not match date of birth (calculated age: {age})'
                })
        
        if self.date_departed and self.date_departed < self.date_admitted:
            raise ValidationError({
                'date_departed': 'Departure date cannot be before admission date'
            })
    
    @property
    def current_age(self):
        """Calculate current age"""
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return self.age
    
    @property
    def years_in_care(self):
        """Calculate years in care"""
        today = timezone.now().date()
        years = today.year - self.date_admitted.year - (
            (today.month, today.day) < (self.date_admitted.month, self.date_admitted.day)
        )
        return max(0, years)
    
    @property
    def can_display_photo(self):
        """Check if photo can be displayed publicly"""
        return self.photo_consent and self.is_published
    
    @property
    def can_display_story(self):
        """Check if story can be displayed publicly"""
        return self.story_consent and self.is_published and self.is_published
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('children:detail', kwargs={'slug': self.slug})


class ChildPhoto(models.Model):
    """Photos of children with privacy controls"""
    PHOTO_TYPE_CHOICES = [
        ('profile', 'Profile Photo'),
        ('activity', 'Activity Photo'),
        ('educational', 'Educational Photo'),
        ('portrait', 'Portrait'),
        ('other', 'Other'),
    ]
    
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='photos')
    photo = models.ImageField(upload_to='children/photos/')
    photo_type = models.CharField(max_length=20, choices=PHOTO_TYPE_CHOICES, default='activity')
    caption = models.CharField(max_length=200, blank=True)
    
    # Privacy Controls
    is_approved = models.BooleanField(default=False, help_text="Approved by staff for display")
    requires_blur = models.BooleanField(default=False, help_text="Face needs to be blurred")
    blur_applied = models.BooleanField(default=False, help_text="Face blur has been applied")
    can_display_publicly = models.BooleanField(default=False, 
                                              help_text="Can be displayed on public website")
    
    # Display Controls
    is_featured = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', '-created_at']
    
    def __str__(self):
        return f"Photo of {self.child.code_name} - {self.get_photo_type_display()}"
    
    @property
    def can_display(self):
        """Check if photo can be displayed"""
        return (
            self.is_approved and 
            self.child.can_display_photo and
            self.can_display_publicly
        )


class ChildStory(models.Model):
    """Stories and updates about children"""
    STORY_TYPE_CHOICES = [
        ('background', 'Background Story'),
        ('achievement', 'Achievement'),
        ('milestone', 'Milestone'),
        ('update', 'Regular Update'),
        ('success', 'Success Story'),
    ]
    
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='stories')
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    story_type = models.CharField(max_length=20, choices=STORY_TYPE_CHOICES, default='update')
    content = models.TextField()
    excerpt = models.TextField(blank=True, help_text="Short excerpt for listings")
    
    # Privacy Controls
    is_approved = models.BooleanField(default=False, help_text="Approved by staff for display")
    can_display_publicly = models.BooleanField(default=False, 
                                              help_text="Can be displayed on public website")
    
    # Associated Photos
    photos = models.ManyToManyField(ChildPhoto, blank=True, related_name='stories')
    
    # Display Controls
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', '-created_at']
        verbose_name_plural = "Child Stories"
    
    def __str__(self):
        return f"{self.title} - {self.child.code_name}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.child.code_name}-{self.title}")
        
        # Ensure unique slug
        original_slug = self.slug
        counter = 1
        while ChildStory.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            self.slug = f"{original_slug}-{counter}"
            counter += 1
        
        if not self.excerpt and self.content:
            self.excerpt = self.content[:200] + "..." if len(self.content) > 200 else self.content
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('children:story_detail', kwargs={'slug': self.slug})


class Need(models.Model):
    """Specific needs of children for sponsorship"""
    NEED_TYPE_CHOICES = [
        ('education', 'Education'),
        ('health', 'Healthcare'),
        ('food', 'Food & Nutrition'),
        ('clothing', 'Clothing'),
        ('shelter', 'Shelter'),
        ('extracurricular', 'Extracurricular Activities'),
        ('counseling', 'Counseling & Therapy'),
        ('other', 'Other'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low Priority'),
        ('medium', 'Medium Priority'),
        ('high', 'High Priority'),
        ('urgent', 'Urgent'),
    ]
    
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='needs')
    title = models.CharField(max_length=200)
    need_type = models.CharField(max_length=20, choices=NEED_TYPE_CHOICES)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Funding Information
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2)
    amount_raised = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_fully_funded = models.BooleanField(default=False)
    
    # Timeline
    start_date = models.DateField(null=True, blank=True)
    expected_completion = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending Funding'),
        ('funded', 'Fully Funded'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    
    # Display
    is_public = models.BooleanField(default=False, help_text="Visible to public for sponsorship")
    display_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['priority', 'display_order', '-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.child.code_name}"
    
    def save(self, *args, **kwargs):
        # Update is_fully_funded based on amount raised
        if self.amount_raised >= self.estimated_cost:
            self.is_fully_funded = True
            if self.status == 'pending':
                self.status = 'funded'
        else:
            self.is_fully_funded = False
        
        super().save(*args, **kwargs)
    
    @property
    def progress_percentage(self):
        if self.estimated_cost == 0:
            return 0
        return min(100, (self.amount_raised / self.estimated_cost) * 100)
    
    @property
    def amount_needed(self):
        return max(0, self.estimated_cost - self.amount_raised)


class Sponsorship(models.Model):
    """Sponsorship relationships between donors and children"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending', 'Pending Approval'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='sponsorships')
    sponsor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                              related_name='sponsorships')
    
    # Sponsorship Details
    sponsorship_type = models.CharField(max_length=20, choices=[
        ('full', 'Full Sponsorship'),
        ('partial', 'Partial Sponsorship'),
        ('education', 'Education Only'),
        ('health', 'Healthcare Only'),
        ('other', 'Other'),
    ])
    monthly_amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Communication Preferences
    can_receive_updates = models.BooleanField(default=True)
    can_send_messages = models.BooleanField(default=True)
    communication_frequency = models.CharField(max_length=20, choices=[
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('biannual', 'Twice a Year'),
        ('annual', 'Yearly'),
    ], default='monthly')
    
    # Payment Information
    is_recurring = models.BooleanField(default=True)
    payment_method = models.CharField(max_length=20, choices=Donation.PAYMENT_METHODS)
    last_payment_date = models.DateField(null=True, blank=True)
    next_payment_date = models.DateField(null=True, blank=True)
    
    # Administrative
    notes = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                  null=True, blank=True, related_name='approved_sponsorships')
    approved_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Sponsorships"
        unique_together = ['child', 'sponsor', 'status']
    
    def __str__(self):
        return f"{self.sponsor.email} sponsors {self.child.code_name}"
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def total_paid(self):
        # This would sum related donations in production
        return 0
    
    @property
    def months_sponsored(self):
        if self.start_date:
            today = timezone.now().date()
            months = (today.year - self.start_date.year) * 12 + today.month - self.start_date.month
            return max(0, months)
        return 0


class ChildUpdate(models.Model):
    """Regular updates sent to sponsors"""
    UPDATE_TYPE_CHOICES = [
        ('progress', 'Progress Report'),
        ('academic', 'Academic Update'),
        ('health', 'Health Update'),
        ('personal', 'Personal Growth'),
        ('event', 'Special Event'),
        ('holiday', 'Holiday Greeting'),
    ]
    
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='updates')
    title = models.CharField(max_length=200)
    update_type = models.CharField(max_length=20, choices=UPDATE_TYPE_CHOICES)
    content = models.TextField()
    
    # Privacy
    is_approved = models.BooleanField(default=False)
    can_share_publicly = models.BooleanField(default=False)
    
    # Associated Media
    photos = models.ManyToManyField(ChildPhoto, blank=True)
    
    # Delivery
    sent_to_sponsors = models.BooleanField(default=False)
    sent_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.child.code_name}"