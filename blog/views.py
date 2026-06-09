import json
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django.utils import timezone

from .models import Post, Category, Tag, Comment, SocialShare
from .forms import CommentForm


def staff_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)
    return wrapper


def get_published_posts():
    """Get all published posts with proper date filtering"""
    now = timezone.now()
    return Post.objects.filter(
        status=Post.Status.PUBLISHED,
        published_at__lte=now
    ).select_related('category').prefetch_related('tags')


def get_recent_posts(limit=5, exclude_post=None):
    posts = get_published_posts()
    if exclude_post:
        posts = posts.exclude(id=exclude_post.id)
    return posts[:limit]


def get_featured_posts(limit=3):
    return get_published_posts().filter(is_featured=True)[:limit]


def get_categories_with_counts():
    return Category.objects.annotate(
        post_count=Count('posts', filter=Q(posts__status=Post.Status.PUBLISHED, posts__published_at__lte=timezone.now()))
    ).filter(post_count__gt=0)


def get_tags_with_counts(limit=10):
    return Tag.objects.annotate(
        post_count=Count('posts', filter=Q(posts__status=Post.Status.PUBLISHED, posts__published_at__lte=timezone.now()))
    ).filter(post_count__gt=0).order_by('-post_count')[:limit]


@require_GET
def post_list(request):
    """List view for blog posts"""
    posts = get_published_posts()
    
    # Get sorting parameter
    order = request.GET.get('order', 'newest')
    if order == 'popular':
        posts = posts.order_by('-view_count', '-published_at')
    else:
        posts = posts.order_by('-published_at')
    
    # Search functionality
    q = request.GET.get('q')
    if q:
        posts = posts.filter(
            Q(title__icontains=q) |
            Q(excerpt__icontains=q) |
            Q(content__icontains=q)
        )
    
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': get_categories_with_counts(),
        'popular_tags': get_tags_with_counts(),
        'featured_posts': get_featured_posts(),
    }
    return render(request, 'blog/post_list.html', context)


@cache_page(60 * 15)
@require_GET
def post_detail(request, slug):
    """Detail view for a blog post"""
    post = get_object_or_404(
        Post.objects.filter(
            status=Post.Status.PUBLISHED,
            published_at__lte=timezone.now()
        ),
        slug=slug
    )
    
    # Increment view count
    post.increment_view_count()
    
    # Related data
    recent_posts = get_recent_posts(limit=3, exclude_post=post)
    comments = post.comments.filter(status=Comment.Status.APPROVED)
    
    # Social sharing URLs
    current_url = request.build_absolute_uri()
    social_share_urls = {
        'facebook': f'https://www.facebook.com/sharer/sharer.php?u={current_url}',
        'twitter': f'https://twitter.com/intent/tweet?url={current_url}&text={post.title}',
        'linkedin': f'https://www.linkedin.com/shareArticle?mini=true&url={current_url}&title={post.title}',
        'whatsapp': f'https://wa.me/?text={post.title}%20{current_url}',
    }
    
    context = {
        'post': post,
        'recent_posts': recent_posts,
        'comments': comments,
        'comment_form': CommentForm(),
        'social_share_urls': social_share_urls,
    }
    return render(request, 'blog/post_detail.html', context)


@require_GET
def category_post_list(request, slug):
    """List posts by category"""
    category = get_object_or_404(Category, slug=slug)
    posts = get_published_posts().filter(category=category)
    
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'category': category,
        'categories': get_categories_with_counts(),
        'popular_tags': get_tags_with_counts(),
        'featured_posts': get_featured_posts(),
    }
    return render(request, 'blog/post_list.html', context)


@require_GET
def tag_post_list(request, slug):
    """List posts by tag"""
    tag = get_object_or_404(Tag, slug=slug)
    posts = get_published_posts().filter(tags=tag)
    
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tag': tag,
        'page_obj': page_obj,
        'categories': get_categories_with_counts(),
        'popular_tags': get_tags_with_counts(),
        'featured_posts': get_featured_posts(),
    }
    return render(request, 'blog/post_list.html', context)


@require_POST
def add_comment(request, slug):
    """Submit a comment on a post"""
    post = get_object_or_404(Post, slug=slug, status=Post.Status.PUBLISHED)
    form = CommentForm(request.POST)
    
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.ip_address = request.META.get('REMOTE_ADDR')
        comment.user_agent = request.META.get('HTTP_USER_AGENT', '')
        if request.user.is_authenticated:
            comment.user = request.user
            comment.name = request.user.get_full_name() or request.user.username
            comment.email = request.user.email
        comment.save()
        messages.success(request, 'Your comment has been submitted and will appear after moderation.')
    else:
        messages.error(request, 'Please correct the errors below.')
    
    return redirect(post.get_absolute_url())


@login_required
@staff_required
def comment_moderation_list(request):
    """List pending comments for moderation"""
    pending_comments = Comment.objects.filter(status=Comment.Status.PENDING).order_by('created_at')
    context = {'comments': pending_comments}
    return render(request, 'blog/comment_moderation.html', context)


@require_POST
@login_required
@staff_required
def moderate_comment(request, comment_id):
    """Approve/reject/spam a comment"""
    comment = get_object_or_404(Comment, id=comment_id)
    action = request.POST.get('action')
    
    if action == 'approve':
        comment.approve(request.user)
        messages.success(request, 'Comment approved.')
    elif action == 'reject':
        comment.reject(request.user)
        messages.success(request, 'Comment rejected.')
    elif action == 'spam':
        comment.status = Comment.Status.SPAM
        comment.save()
        messages.success(request, 'Comment marked as spam.')
    else:
        messages.error(request, 'Invalid action.')
    
    return redirect('blog:comment_moderation')


@csrf_exempt
@require_POST
def track_social_share(request):
    """Track social media shares via AJAX"""
    try:
        data = json.loads(request.body)
        post_id = data.get('post_id')
        platform = data.get('platform')
        
        post = get_object_or_404(Post, id=post_id)
        SocialShare.objects.create(
            post=post,
            platform=platform,
            shared_by=request.user if request.user.is_authenticated else None,
            ip_address=request.META.get('REMOTE_ADDR'),
        )
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    
@require_GET
def search_posts(request):
    """Search blog posts"""
    query = request.GET.get('q', '')
    posts = get_published_posts()
    
    if query:
        posts = posts.filter(
            Q(title__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(content__icontains=query) |
            Q(author__icontains=query)
        )
    
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'categories': get_categories_with_counts(),
        'popular_tags': get_tags_with_counts(),
        'featured_posts': get_featured_posts(),
    }
    return render(request, 'blog/post_list.html', context)