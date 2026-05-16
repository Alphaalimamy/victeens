from django.db import models
from django.utils.text import slugify


class SiteSettings(models.Model):
    """Global site settings"""
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
    
    # Transparency
    show_live_donations = models.BooleanField(default=True)
    show_impact_stats = models.BooleanField(default=True)
    
    # Maintenance
    site_maintenance = models.BooleanField(default=False)
    maintenance_message = models.TextField(blank=True)
    
    # SEO
    meta_description = models.TextField(blank=True)
    meta_keywords = models.TextField(blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
    
    def __str__(self):
        return self.site_name
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.__class__.objects.exclude(id=self.id).delete()
        super().save(*args, **kwargs)
    
    @classmethod
    def load(cls):
        try:
            return cls.objects.get()
        except cls.DoesNotExist:
            return cls.objects.create()


class ImpactStat(models.Model):
    """Impact statistics to display on homepage"""
    title = models.CharField(max_length=100)
    value = models.IntegerField()
    suffix = models.CharField(max_length=10, blank=True, help_text="E.g., +, %, K")
    icon = models.CharField(max_length=50, help_text="Font Awesome class, e.g., fas fa-heart")
    description = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'title']
        verbose_name = "Impact Statistic"
        verbose_name_plural = "Impact Statistics"
    
    def __str__(self):
        return self.title


class Program(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to="programs/", blank=True, null=True)

    # Tailwind gradient utility classes
    gradient_color = models.CharField(max_length=100, help_text="Example: from-vto-orange to-vto-orange-golden")

    # FontAwesome icon class
    icon_class = models.CharField(max_length=100, help_text="Example: fas fa-book-open")

    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        return ""


class ProgramFeature(models.Model):
    program = models.ForeignKey(
        Program,
        related_name="features",
        on_delete=models.CASCADE)
    text = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.program.title} – {self.text}"



class Testimonial(models.Model):
    """Testimonials from donors, volunteers, or community"""
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100, blank=True, help_text="E.g., Donor, Volunteer, Parent")
    content = models.TextField()
    image = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.role}"


class FAQ(models.Model):
    """Frequently Asked Questions"""
    question = models.CharField(max_length=200)
    answer = models.TextField()
    category = models.CharField(max_length=50, choices=[
        ('general', 'General'),
        ('donation', 'Donations'),
        ('volunteer', 'Volunteering'),
        ('child', 'Child Sponsorship'),
        ('other', 'Other'),
    ], default='general')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['category', 'order', 'question']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
    
    def __str__(self):
        return self.question


class Page(models.Model):
    """Dynamic pages like About, Contact, etc."""
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    is_published = models.BooleanField(default=True)
    show_in_navigation = models.BooleanField(default=False)
    navigation_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['navigation_order', 'title']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class ContactMessage(models.Model):
    """Contact form submissions"""
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
    
    def __str__(self):
        return f"{self.name} - {self.subject}"
    


class Milestone(models.Model):
    year = models.PositiveIntegerField()
    title = models.CharField(max_length=100)
    description = models.TextField()
    highlight_stats = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional stats e.g. '2,500 children, 850+ volunteers'"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Controls display order in the timeline"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "year"]

    def __str__(self):
        return f"{self.year} – {self.title}"


class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    bio = models.TextField()
    image = models.ImageField(upload_to="team/")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name
    
    
class OrganizationProfile(models.Model):
    mission = models.TextField()
    vision = models.TextField()
    image = models.ImageField(upload_to="profile/", blank=True, null=True)
    
    def __str__(self):
        return "Organization Profile"

class CoreValue(models.Model):
    title = models.CharField(max_length=50)
    icon = models.CharField(
        max_length=100,
        help_text="Font Awesome icon class (e.g. fas fa-heart)"
    )
    description = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title
