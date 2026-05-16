"""
Service layer for business logic - following Repository/Service pattern
"""
from django.core.cache import cache
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q, Count
from django.conf import settings
from .models import Post, Category, Tag, Comment, PostView
import logging

logger = logging.getLogger(__name__)


class BlogService:
    """Service class for blog operations"""
    
    @staticmethod
    def get_published_posts():
        """Get all published posts"""
        return Post.objects.filter(status=Post.Status.PUBLISHED,
                                   published_date__lte=timezone.now()).select_related('author', 'category').prefetch_related('tags')
    
    @staticmethod
    def get_featured_posts(limit=3):
        """Get featured posts with caching"""
        cache_key = f'blog:featured_posts:{limit}'
        cached = cache.get(cache_key)
        
        if cached is not None:
            return cached
        
        posts = BlogService.get_published_posts().filter(is_featured=True).order_by('-published_date')[:limit]
        
        cache.set(cache_key, posts, timeout=3600)  # Cache for 1 hour
        return posts
    
    @staticmethod
    def get_recent_posts(limit=5, exclude_post=None):
        """Get recent posts excluding specific post"""
        queryset = BlogService.get_published_posts()
        if exclude_post:
            queryset = queryset.exclude(id=exclude_post.id)
        return queryset.order_by('-published_date')[:limit]
    
    @staticmethod
    def get_post_by_slug(slug=None):
        """Get post by slug and date"""
        try:
            queryset = Post.objects.select_related('author', 'category').prefetch_related('tags')
            
            post = queryset.get(slug=slug, status=Post.Status.PUBLISHED)
            
            return post
        except Post.DoesNotExist:
            return None
    
    @staticmethod
    def increment_post_view(post, request):
        """Increment view count for a post"""
        if not request.session.session_key:
            request.session.create()
        
        session_key = request.session.session_key
        
        # Check if this session has already viewed this post
        if not PostView.objects.filter(post=post, session_key=session_key).exists():
            PostView.objects.create(
                post=post,
                session_key=session_key,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                referrer=request.META.get('HTTP_REFERER', '')
            )
            post.increment_view_count()
    
    @staticmethod
    def get_approved_comments(post):
        """Get approved comments for a post"""
        return post.comments.filter(status=Comment.Status.APPROVED).select_related('user')
    
    @staticmethod
    def search_posts(query, category=None, tag=None, date_from=None, date_to=None):
        """Search posts with filters"""
        queryset = BlogService.get_published_posts()
        
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(excerpt__icontains=query) |
                Q(content__icontains=query) |
                Q(tags__name__icontains=query)
            ).distinct()
        
        if category:
            queryset = queryset.filter(category=category)
        
        if tag:
            queryset = queryset.filter(tags=tag)
        
        if date_from:
            queryset = queryset.filter(published_date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(published_date__lte=date_to)
        
        return queryset
    
    @staticmethod
    def get_popular_posts(limit=5, days=30):
        """Get popular posts based on views in last N days"""
        time_threshold = timezone.now() - timezone.timedelta(days=days)
        
        return BlogService.get_published_posts().filter(
            postview__created_at__gte=time_threshold
        ).annotate(
            recent_views=Count('postview')
        ).order_by('-recent_views', '-published_date')[:limit]
    
    @staticmethod
    def get_categories_with_counts():
        """Get all categories with post counts"""
        return Category.objects.annotate(
            post_count=Count('posts', filter=Q(posts__status=Post.Status.PUBLISHED))
        ).filter(post_count__gt=0).order_by('name')
    
    @staticmethod
    def get_tags_with_counts(limit=20):
        """Get popular tags with counts"""
        return Tag.objects.annotate(
            post_count=Count('posts', filter=Q(posts__status=Post.Status.PUBLISHED))
        ).filter(post_count__gt=0).order_by('-post_count', 'name')[:limit]


class CommentService:
    """Service class for comment operations"""
    
    @staticmethod
    def create_comment(post, data, request):
        """Create a new comment"""
        from .forms import CommentForm
        
        form = CommentForm(data, post=post, request=request)
        if form.is_valid():
            comment = form.save()
            
            # Auto-approve comments from authenticated users
            if request.user.is_authenticated:
                comment.approve(request.user)
            
            return comment, form
        return None, form
    
    @staticmethod
    def get_pending_comments():
        """Get comments pending moderation"""
        return Comment.objects.filter(status=Comment.Status.PENDING).select_related('post', 'user')
    
    @staticmethod
    def moderate_comment(comment, status, moderator, notes=''):
        """Moderate a comment"""
        if status == 'approve':
            comment.approve(moderator)
        elif status == 'reject':
            comment.reject(moderator, notes)
        elif status == 'spam':
            comment.status = Comment.Status.SPAM
            comment.moderated_by = moderator
            comment.moderated_at = timezone.now()
            comment.moderation_notes = notes
            comment.save()


class AnalyticsService:
    """Service for blog analytics"""
    
    @staticmethod
    def get_post_analytics(post):
        """Get analytics for a specific post"""
        views_today = PostView.objects.filter(
            post=post,
            created_at__date=timezone.now().date()
        ).count()
        
        views_week = PostView.objects.filter(
            post=post,
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).count()
        
        return {
            'total_views': post.view_count,
            'views_today': views_today,
            'views_week': views_week,
            'total_comments': post.comments.filter(status=Comment.Status.APPROVED).count(),
            'total_shares': post.social_shares.count(),
        }
    
    @staticmethod
    def get_platform_shares(post):
        """Get breakdown of shares by platform"""
        from django.db.models import Count
        return post.social_shares.values('platform').annotate(count=Count('platform')).order_by('-count')