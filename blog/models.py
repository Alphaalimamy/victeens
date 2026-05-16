from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone

User = get_user_model()
# In models.py

class Category(models.Model):
    """Category model for blog posts"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    # FIXED: Changed 'category_detail' to 'category_post_list'
    def get_absolute_url(self):
        return reverse('blog:category_post_list', kwargs={'slug': self.slug})


class Tag(models.Model):
    """Tag model for blog posts"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    # FIXED: Changed 'tag_detail' to 'tag_post_list'
    def get_absolute_url(self):
        return reverse('blog:tag_post_list', kwargs={'slug': self.slug})
    


class Post(models.Model):
    """Main blog post model"""
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'
    
    class PostType(models.TextChoices):
        ARTICLE = 'article', 'Article'
        NEWS = 'news', 'News'
        ANNOUNCEMENT = 'announcement', 'Announcement'
        UPDATE = 'update', 'Update'
    
    # Basic information
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique_for_date='published_date')
    excerpt = models.TextField(max_length=300, help_text="Short excerpt for preview")
    content = models.TextField()
    
    # Relationships
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='posts')
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')
    
    # Media
    featured_image = models.ImageField(upload_to='blog/featured_images/%Y/%m/%d/', blank=True)
    thumbnail_image = models.ImageField(upload_to='blog/thumbnails/%Y/%m/%d/', blank=True)
    
    # Metadata
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    post_type = models.CharField(max_length=20, choices=PostType.choices, default=PostType.ARTICLE)
    is_featured = models.BooleanField(default=False)
    allow_comments = models.BooleanField(default=True)
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_date = models.DateTimeField(null=True, blank=True)
    
    # SEO fields
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=300, blank=True)
    
    # Statistics
    view_count = models.PositiveIntegerField(default=0)
    share_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-published_date', '-created_at']
        indexes = [
            models.Index(fields=['-published_date', 'status']),
            models.Index(fields=['slug']),
            models.Index(fields=['author']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Set published_date when status changes to published
        if self.status == self.Status.PUBLISHED and not self.published_date:
            self.published_date = timezone.now()
        
        # Generate meta fields if empty
        if not self.meta_title:
            self.meta_title = self.title
        if not self.meta_description and self.excerpt:
            self.meta_description = self.excerpt[:160]
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
      
        return reverse('blog:post_detail', kwargs={'slug': self.slug})
    
    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED and self.published_date <= timezone.now()
    
    @property
    def reading_time(self):
        """Calculate estimated reading time (200 words per minute)"""
        word_count = len(self.content.split())
        minutes = max(1, round(word_count / 200))
        return f"{minutes} min read"


class Comment(models.Model):
    """Comment system for blog posts with moderation"""
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending Review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        SPAM = 'spam', 'Spam'
    
    # Core fields
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # Commenter information
    name = models.CharField(max_length=100)
    email = models.EmailField()
    website = models.URLField(blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='comments')
    
    # Content
    content = models.TextField(max_length=1000)
    
    # Moderation
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    moderated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderated_comments')
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderation_notes = models.TextField(blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Comment by {self.name} on {self.post.title}"
    
    def is_reply(self):
        return self.parent is not None
    
    @property
    def display_name(self):
        if self.user:
            return self.user.get_full_name() or self.user.username
        return self.name
    
    def approve(self, moderator):
        self.status = self.Status.APPROVED
        self.moderated_by = moderator
        self.moderated_at = timezone.now()
        self.save()
    
    def reject(self, moderator, notes=''):
        self.status = self.Status.REJECTED
        self.moderated_by = moderator
        self.moderated_at = timezone.now()
        self.moderation_notes = notes
        self.save()


class PostView(models.Model):
    """Track post views for analytics"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='views')
    session_key = models.CharField(max_length=40, db_index=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['post', 'session_key']
        indexes = [
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"View of {self.post.title}"


class SocialShare(models.Model):
    """Track social media shares"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='social_shares')
    platform = models.CharField(max_length=50)  # facebook, twitter, linkedin, etc.
    shared_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    shared_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['post', 'platform']),
        ]


# Signals for automatic actions
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.cache import cache

@receiver(post_save, sender=Post)
def clear_blog_cache(sender, instance, **kwargs):
    """Clear cache when posts are saved"""
    cache_keys = [
        'blog:featured_posts',
        'blog:recent_posts',
        'blog:categories',
        f'blog:post_{instance.id}',
    ]
    for key in cache_keys:
        cache.delete(key)

@receiver(post_save, sender=Comment)
def send_comment_notification(sender, instance, created, **kwargs):
    """Send notifications for new comments"""
    if created and instance.post.author.notification_preferences.get('new_comment', True):
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = f'New comment on your post: {instance.post.title}'
        message = f"""
        New comment from {instance.name}:
        
        {instance.content}
        
        To moderate this comment, visit: {settings.SITE_URL}{instance.post.get_absolute_url()}
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [instance.post.author.email],
            fail_silently=True,
        )