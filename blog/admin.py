from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from .models import Post, Category, Tag, Comment, PostView, SocialShare
from .forms import CommentModerationForm


class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'status', 'is_featured', 'published_date', 'view_count', 'admin_actions')
    list_filter = ('status', 'category', 'is_featured', 'post_type', 'created_at')
    search_fields = ('title', 'content', 'excerpt', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('view_count', 'share_count', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'excerpt', 'content', 'author', 'category', 'tags')
        }),
        ('Media', {
            'fields': ('featured_image', 'thumbnail_image'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('status', 'post_type', 'is_featured', 'allow_comments', 'published_date')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('view_count', 'share_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['make_published', 'make_draft', 'make_featured', 'remove_featured']
    
    def make_published(self, request, queryset):
        updated = queryset.update(status=Post.Status.PUBLISHED)
        self.message_user(request, f'{updated} posts were successfully published.')
    make_published.short_description = "Mark selected posts as published"
    
    def make_draft(self, request, queryset):
        updated = queryset.update(status=Post.Status.DRAFT)
        self.message_user(request, f'{updated} posts were marked as draft.')
    make_draft.short_description = "Mark selected posts as draft"
    
    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} posts were marked as featured.')
    make_featured.short_description = "Mark selected posts as featured"
    
    def remove_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} posts were removed from featured.')
    remove_featured.short_description = "Remove selected posts from featured"
    
    def admin_actions(self, obj):
        return format_html(
            '<a class="button" href="{}">View</a>&nbsp;'
            '<a class="button" href="{}">Edit</a>',
            obj.get_absolute_url(),
            reverse('admin:blog_post_change', args=[obj.id])
        )
    admin_actions.short_description = 'Actions'


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


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'post_count', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    
    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Posts'


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'post_count', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    
    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Posts'


class PostViewAdmin(admin.ModelAdmin):
    list_display = ('post', 'ip_address', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('post__title', 'ip_address')
    readonly_fields = ('post', 'session_key', 'ip_address', 'user_agent', 'referrer', 'created_at')


class SocialShareAdmin(admin.ModelAdmin):
    list_display = ('post', 'platform', 'shared_by', 'shared_at')
    list_filter = ('platform', 'shared_at')
    search_fields = ('post__title', 'platform')


admin.site.register(Post, PostAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(PostView, PostViewAdmin)
admin.site.register(SocialShare, SocialShareAdmin)