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
    content = RichTextUploadingField(
        config_name='default',
        help_text="Rich text editor – add images, videos, lists, etc."
    )

    # Author & taxonomy
    author = models.CharField(max_length=100, blank=True, default='Victory Teens Organization')
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

        if not self.author:
            self.author = 'Victory Teens Organization'

        # Auto-set published_at when status changes to PUBLISHED
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()

        if not self.excerpt and self.content:
            from django.utils.html import strip_tags
            plain = strip_tags(self.content)
            self.excerpt = plain[:250] + ('…' if len(plain) > 250 else '')

        if not self.meta_description and self.excerpt:
            self.meta_description = self.excerpt[:160]

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})

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
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending Review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        SPAM = 'spam', 'Spam'
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='comments')
    content = models.TextField(max_length=1000)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    moderated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderated_comments')
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderation_notes = models.TextField(blank=True)
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
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='social_shares')
    platform = models.CharField(max_length=50)
    shared_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    shared_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['post', 'platform']),
        ]