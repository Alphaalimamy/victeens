# admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Post, PostImage, Category, Tag, Comment, PostView, SocialShare
from .forms import CommentModerationForm


class PostImageInline(admin.TabularInline):
    """Inline gallery images for the post"""
    model = PostImage
    extra = 1
    fields = ['image', 'alt_text', 'caption', 'order']
    ordering = ['order']


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'status', 'published_at', 'is_featured', 'view_count', 'preview_hero']
    list_filter = ['status', 'is_featured', 'category', 'published_at', 'author']
    search_fields = ['title', 'excerpt', 'content', 'seo_title', 'meta_description']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    raw_id_fields = ['author']
    inlines = [PostImageInline]
    
    fieldsets = (
        ('Basic Content', {
            'fields': ('title', 'slug', 'author', 'category', 'tags', 'excerpt', 'content')
        }),
        ('Media', {
            'fields': ('hero_image', 'hero_caption', 'video_url', 'og_image'),
            'classes': ('wide',),
            'description': 'Hero image appears at top of post. OG image used for social sharing.'
        }),
        ('SEO & Metadata', {
            'fields': ('seo_title', 'meta_description'),
            'classes': ('collapse',),
        }),
        ('Publishing Options', {
            'fields': ('status', 'published_at', 'is_featured', 'allow_comments'),
        }),
        ('Statistics', {
            'fields': ('view_count',),
            'classes': ('collapse',),
            'description': 'Auto‑incremented when a post is viewed.'
        }),
    )
    
    readonly_fields = ['view_count', 'created_at', 'updated_at']
    actions = ['make_published', 'make_featured']
    
    def preview_hero(self, obj):
        if obj.hero_image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit:cover;"/>', obj.hero_image.url)
        return "No image"
    preview_hero.short_description = 'Hero preview'
    
    def make_published(self, request, queryset):
        queryset.update(status=Post.Status.PUBLISHED)
    make_published.short_description = "Mark selected posts as published"
    
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
    make_featured.short_description = "Mark selected posts as featured"


@admin.register(PostImage)
class PostImageAdmin(admin.ModelAdmin):
    list_display = ['post', 'order', 'alt_text', 'thumbnail_preview']
    list_filter = ['post']
    search_fields = ['alt_text', 'caption']
    
    def thumbnail_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="40" height="40" style="object-fit:cover;"/>', obj.image.url)
        return "No image"
    thumbnail_preview.short_description = 'Preview'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'post_count', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    
    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Number of posts'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'post_count', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    
    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Number of posts'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('name', 'post_link', 'content_preview', 'status', 'created_at', 'admin_actions')
    list_filter = ('status', 'created_at', 'post')
    search_fields = ('name', 'email', 'content', 'post__title')
    readonly_fields = ('ip_address', 'user_agent', 'created_at', 'updated_at')
    actions = ['approve_comments', 'reject_comments', 'mark_as_spam']
    form = CommentModerationForm
    
    def post_link(self, obj):
        return format_html('<a href="{}">{}</a>', 
                          reverse('admin:blog_post_change', args=[obj.post.id]),
                          obj.post.title[:50])
    post_link.short_description = 'Post'
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Comment'
    
    def approve_comments(self, request, queryset):
        for comment in queryset:
            comment.approve(request.user)
        self.message_user(request, f'{queryset.count()} comments approved.')
    approve_comments.short_description = "Approve selected comments"
    
    def reject_comments(self, request, queryset):
        for comment in queryset:
            comment.reject(request.user)
        self.message_user(request, f'{queryset.count()} comments rejected.')
    reject_comments.short_description = "Reject selected comments"
    
    def mark_as_spam(self, request, queryset):
        updated = queryset.update(status=Comment.Status.SPAM)
        self.message_user(request, f'{updated} comments marked as spam.')
    mark_as_spam.short_description = "Mark selected comments as spam"
    
    def admin_actions(self, obj):
        return format_html(
            '<a class="button" href="{}">Edit</a>',
            reverse('admin:blog_comment_change', args=[obj.id])
        )
    admin_actions.short_description = 'Actions'


@admin.register(PostView)
class PostViewAdmin(admin.ModelAdmin):
    list_display = ('post', 'ip_address', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('post__title', 'ip_address')
    readonly_fields = ('post', 'session_key', 'ip_address', 'user_agent', 'referrer', 'created_at')


@admin.register(SocialShare)
class SocialShareAdmin(admin.ModelAdmin):
    list_display = ('post', 'platform', 'shared_by', 'shared_at')
    list_filter = ('platform', 'shared_at')
    search_fields = ('post__title', 'platform')