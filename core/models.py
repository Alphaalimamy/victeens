from django.db import models
from django.utils.text import slugify
from django.utils.safestring import mark_safe
from django.urls import reverse
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField  # Optional: for image uploads


class SiteConfiguration(models.Model):
    """
    Homepage hero content and main stats.
    Only one instance should exist.
    """
    hero_badge = models.CharField(max_length=100, default="Empowering Tomorrow's Leaders")
    hero_title = models.CharField(max_length=200, default="Every Teen deserves a brighter future.")
    hero_subtitle = models.TextField(
        default="We transform the lives of orphaned and underprivileged teens through education, mentorship, life skills, and a safe community where every young person can thrive."
    )
    hero_image = models.ImageField(upload_to='hero/', blank=True, null=True,
                                   help_text="Recommended size: 800x520px")
    
    years_of_impact = models.PositiveSmallIntegerField(default=15)
    lives_supported = models.PositiveIntegerField(default=1200)
    partners_count = models.PositiveSmallIntegerField(default=30)
    
    primary_cta_text = models.CharField(max_length=50, default="Our Story")
    primary_cta_url_name = models.CharField(max_length=100, default="about")
    secondary_cta_text = models.CharField(max_length=50, default="Volunteer")
    secondary_cta_url_name = models.CharField(max_length=100, default="volunteer")
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configuration"
    
    def __str__(self):
        return "Homepage Hero & Stats"
    
    def save(self, *args, **kwargs):
        if not self.pk and SiteConfiguration.objects.exists():
            raise ValueError("Only one SiteConfiguration instance allowed.")
        super().save(*args, **kwargs)
    
    def hero_image_preview(self):
        if self.hero_image:
            return mark_safe(f'<img src="{self.hero_image.url}" width="150" />')
        return "No image"
    hero_image_preview.short_description = "Hero Preview"


class SiteSettings(models.Model):
    """
    Global site settings (contact, social, SEO).
    Only one instance should exist.
    """
    site_name = models.CharField(max_length=200, default="Victory Teens Organization")
    tagline = models.CharField(max_length=300, default="Providing hope and future for orphaned teens")
    contact_email = models.EmailField(default="info@victoryteens.org")
    contact_phone = models.CharField(max_length=20, default="+232 00 000 000")
    address = models.TextField(default="123 Dundas Street, Freetown, Sierra Leone")
    
    # Social Media
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    
    # Donation Settings
    donation_goal = models.DecimalField(max_digits=12, decimal_places=2, default=100000.00)
    donation_currency = models.CharField(max_length=3, default="KES")
    
    show_live_donations = models.BooleanField(default=True)
    show_impact_stats = models.BooleanField(default=True)
    
    site_maintenance = models.BooleanField(default=False)
    maintenance_message = models.TextField(blank=True)
    
    meta_description = models.TextField(blank=True)
    meta_keywords = models.TextField(blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
    
    def __str__(self):
        return self.site_name
    
    def save(self, *args, **kwargs):
        if not self.pk and SiteSettings.objects.exists():
            raise ValueError("Only one SiteSettings instance allowed.")
        super().save(*args, **kwargs)
    
    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create()
        return obj


# ==================== CONTENT MODELS ====================

class ImpactStat(models.Model):
    """Displayed in the stats grid on homepage."""
    title = models.CharField(max_length=100)
    value = models.CharField(max_length=20, help_text="Number or text, e.g., '15'")
    suffix = models.CharField(max_length=10, blank=True, help_text="Optional: +, %, K")
    icon = models.CharField(max_length=50, help_text="Font Awesome class, e.g., 'fas fa-heart'")
    description = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order', 'title']
        verbose_name = "Impact Statistic"
        verbose_name_plural = "Impact Statistics"
        indexes = [models.Index(fields=['is_active', 'order'])]
    
    def __str__(self):
        return f"{self.value}{self.suffix} – {self.title}"


class Program(models.Model):
    """Program cards shown on homepage."""
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = RichTextField(help_text="Program description with rich text formatting")
    image = models.ImageField(upload_to='programs/', blank=True, null=True,
                              help_text="Recommended size: 800x600px")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        indexes = [models.Index(fields=['is_active', 'order'])]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    @property
    def image_url(self):
        """Convenience property for template compatibility."""
        return self.image.url if self.image else ''
    
    def get_absolute_url(self):
        return reverse('program_detail', args=[self.slug])


class ProgramFeature(models.Model):
    """Optional: list of features per program (used in detail page)."""
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='features')
    text = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.program.title}: {self.text}"


class Testimonial(models.Model):
    """Community testimonials – used in the Stories of Hope section."""
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100, blank=True, help_text="e.g., Donor, Volunteer, Parent")
    content = RichTextField(help_text="Testimonial content with rich text formatting")
    image = models.ImageField(upload_to='testimonials/', blank=True, null=True,
                              help_text="Profile photo (square recommended)")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Testimonial"
        verbose_name_plural = "Testimonials"
        indexes = [models.Index(fields=['is_active', 'order'])]
    
    def __str__(self):
        return f"{self.name} – {self.role or 'Community member'}"

class Teen(models.Model):
    """Individual teens supported – for success stories."""
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    photo = models.ImageField(upload_to='teens/', blank=True, null=True)
    age = models.PositiveSmallIntegerField()
    story = RichTextField(help_text="Success story with rich text formatting")
    is_featured = models.BooleanField(default=False)
    joined_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)  # Allow null temporarily
    
    class Meta:
        ordering = ['-joined_date', 'first_name']
        indexes = [models.Index(fields=['is_featured', '-joined_date'])]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.age})"
    
    
class FAQ(models.Model):
    """Model for Frequently Asked Questions"""
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('donation', 'Donations'),
        ('volunteer', 'Volunteering'),
        ('child', 'Child Sponsorship'),
        ('other', 'Other'),
    ]
    question = models.CharField(max_length=200)
    answer = RichTextField(help_text="FAQ answer with rich text formatting")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['category', 'order', 'question']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
        indexes = [models.Index(fields=['category', 'is_active', 'order'])]
    
    def __str__(self):
        return self.question


class Page(models.Model):
    """Dynamic content pages (About, Contact, etc.)"""
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = RichTextField(help_text="Page content with rich text formatting (images, links, etc.)")
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    is_published = models.BooleanField(default=True)
    show_in_navigation = models.BooleanField(default=False)
    navigation_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['navigation_order', 'title']
        indexes = [models.Index(fields=['is_published', 'show_in_navigation'])]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('page_detail', args=[self.slug])


class ContactMessage(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('archived', 'Archived'),
    ]
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='new')
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"
        indexes = [models.Index(fields=['status', '-created_at'])]
    
    def __str__(self):
        return f"{self.name} – {self.subject}"
    
    def mark_as_read(self):
        self.status = 'read'
        self.save()
    
    def mark_as_replied(self):
        self.status = 'replied'
        self.save()


class Milestone(models.Model):
    """Timeline milestones."""
    year = models.PositiveIntegerField()
    title = models.CharField(max_length=100)
    description = RichTextField(help_text="Milestone description with rich text formatting")
    highlight_stats = models.CharField(max_length=255, blank=True,
                                       help_text="Optional stats e.g. '2,500 children, 850+ volunteers'")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'year']
        indexes = [models.Index(fields=['order', 'year'])]
    
    def __str__(self):
        return f"{self.year} – {self.title[:50]}"


class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100, help_text="General role (e.g., 'Executive Director', 'Program Manager')")
    bio = RichTextField(blank=True, help_text="Team member biography with rich text formatting")
    image = models.ImageField(upload_to='team/', blank=True, null=True)
    email = models.EmailField(blank=True)
    linkedin_url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order', 'name']
        indexes = [models.Index(fields=['is_active', 'order'])]
    
    def __str__(self):
        return self.name
    
    @property
    def role_display(self):
        return self.get_role_display()


class OrganizationProfiles(models.Model):
    """Mission & vision (singleton)."""
    history = RichTextField(help_text="Organization history with rich text formatting")
    mission = RichTextField(help_text="Organization mission statement with rich text formatting")
    vision = RichTextField(help_text="Organization vision statement with rich text formatting")
    image = models.ImageField(upload_to='profile/', blank=True, null=True)
    background_image = models.ImageField(upload_to='profile/', blank=True, null=True,
                                         help_text="Background image for mission/vision section")
    
    class Meta:
        verbose_name = "Organization Profile"
        verbose_name_plural = "Organization Profile"
    
    def __str__(self):
        return "Organization Profile"
    
    def save(self, *args, **kwargs):
        if not self.pk and OrganizationProfiles.objects.exists():
            raise ValueError("Only one OrganizationProfile instance allowed.")
        super().save(*args, **kwargs)


class CoreValue(models.Model):
    """Core values displayed on About page - unified model"""
    title = models.CharField(max_length=100)
    icon = models.CharField(max_length=100, help_text="Font Awesome icon class, e.g., 'fas fa-heart'")
    description = RichTextField(help_text="Core value description with rich text formatting")
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order', 'title']
        verbose_name = "Core Value"
        verbose_name_plural = "Core Values"
    
    def __str__(self):
        return self.title


class FocusArea(models.Model):
    """Model for Key Focus Areas"""
    title = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, help_text="Font Awesome icon class (e.g., 'fas fa-home')")
    description = RichTextField(blank=True, help_text="Focus area description with rich text formatting")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order']
        verbose_name = "Focus Area"
        verbose_name_plural = "Focus Areas"
    
    def __str__(self):
        return self.title


class Impact(models.Model):
    """Model for impact statistics - unified version"""
    title = models.CharField(max_length=100)
    value = models.CharField(max_length=50, help_text="e.g., '10,000+' or '50'")
    icon = models.CharField(max_length=50)
    description = RichTextField(blank=True, help_text="Detailed description with rich text formatting")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order']
        verbose_name = "Impact"
        verbose_name_plural = "Impacts"
        indexes = [models.Index(fields=['is_active', 'order'])]
    
    def __str__(self):
        return f"{self.title}: {self.value}"


class Partner(models.Model):
    """Model for partner organizations"""
    PARTNER_TYPE_CHOICES = [
        ('corporate', 'Corporate Partner'),
        ('ngo', 'NGO Partner'),
        ('government', 'Government Partner'),
        ('community', 'Community Partner'),
    ]
    
    name = models.CharField(max_length=100)
    partner_type = models.CharField(max_length=20, choices=PARTNER_TYPE_CHOICES, default='corporate')
    logo = models.ImageField(upload_to='partners/', blank=True, null=True)
    website_url = models.URLField(blank=True)
    description = RichTextField(blank=True, help_text="Partner description with rich text formatting")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    featured = models.BooleanField(default=False, help_text="Show on homepage")
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.name


class NewsletterSubscriber(models.Model):
    """Model for email newsletter subscribers"""
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-subscribed_at']
        verbose_name = "Newsletter Subscriber"
        verbose_name_plural = "Newsletter Subscribers"
    
    def __str__(self):
        return self.email
    
    def unsubscribe(self):
        self.is_active = False
        self.unsubscribed_at = models.DateTimeField(auto_now=True)
        self.save()


class Donation(models.Model):
    """Model for tracking donations"""
    DONATION_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    donor_name = models.CharField(max_length=100)
    donor_email = models.EmailField()
    donor_phone = models.CharField(max_length=20, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    message = models.TextField(blank=True)
    is_anonymous = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=DONATION_STATUS, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['status', '-created_at'])]
    
    def __str__(self):
        return f"{self.donor_name} - {self.amount} {self.currency}"
    
    @property
    def display_name(self):
        return "Anonymous" if self.is_anonymous else self.donor_name