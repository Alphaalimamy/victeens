from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from ckeditor_uploader.fields import RichTextUploadingField

User = get_user_model()

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
    



class PublishedManager(models.Manager):
    def get_queryset(self):
        now = timezone.now()
        return super().get_queryset().filter(
            status=Post.Status.PUBLISHED,
            published_at__lte=now
        )


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'

    # Core
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    excerpt = models.TextField(max_length=300, blank=True)
    content = RichTextUploadingField(  # <-- RICH TEXT
        config_name='default',
        help_text="Rich text editor – add images, videos, lists, etc."
    )

    # Author & taxonomy
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    tags = models.ManyToManyField('Tag', blank=True, related_name='posts')

    # Media
    hero_image = models.ImageField(upload_to='blog/hero/%Y/%m/%d/', blank=True)
    hero_caption = models.CharField(max_length=200, blank=True)
    video_url = models.URLField(blank=True)

    # SEO
    seo_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    og_image = models.ImageField(upload_to='blog/og/%Y/%m/%d/', blank=True)

    # Publishing
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_featured = models.BooleanField(default=False)
    allow_comments = models.BooleanField(default=True)
    view_count = models.PositiveIntegerField(default=0)

    # Managers
    objects = models.Manager()
    live = PublishedManager()

    class Meta:
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        # Auto excerpt (strip HTML from rich text)
        if not self.excerpt and self.content:
            from django.utils.html import strip_tags
            plain = strip_tags(self.content)
            self.excerpt = plain[:250] + ('…' if len(plain) > 250 else '')

        if not self.meta_description and self.excerpt:
            self.meta_description = self.excerpt[:160]

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={
            'year': self.published_at.year,
            'month': self.published_at.month,
            'day': self.published_at.day,
            'slug': self.slug,
        })

    @property
    def reading_time_minutes(self) -> int:
        from django.utils.html import strip_tags
        plain = strip_tags(self.content)
        word_count = len(plain.split())
        return max(1, round(word_count / 200))

    @property
    def is_published(self) -> bool:
        return (self.status == self.Status.PUBLISHED and
                self.published_at <= timezone.now())

    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])


class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField(upload_to='blog/gallery/%Y/%m/%d/')
    alt_text = models.CharField(max_length=200, blank=True)
    caption = models.CharField(max_length=300, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']
        

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