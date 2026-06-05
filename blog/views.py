from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.cache import cache_page
from django.http import HttpResponseForbidden, JsonResponse, Http404
from django.db.models import Q, Count
from django.utils import timezone
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


from .models import Post, Category, Tag, Comment, SocialShare
from .forms import PostForm, CommentForm, CommentModerationForm, SearchForm


# ---------- Helper functions ----------
def staff_required(view_func):
    """Decorator: staff only"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)
    return wrapper


def get_published_posts():
    """Return queryset of published posts (live and scheduled)"""
    return Post.live.all()  # using the custom PublishedManager


def get_recent_posts(limit=5, exclude_post=None):
    """Get most recent published posts"""
    posts = get_published_posts()[:limit]
    if exclude_post:
        posts = posts.exclude(id=exclude_post.id)
    return posts


def get_featured_posts(limit=3):
    """Get featured published posts"""
    return get_published_posts().filter(is_featured=True)[:limit]


def get_categories_with_counts():
    """Return categories with post count (published posts only)"""
    return Category.objects.annotate(
        post_count=Count('posts', filter=Q(posts__status=Post.Status.PUBLISHED))
    ).filter(post_count__gt=0)


def get_tags_with_counts(limit=10):
    """Return tags with post count (published posts only)"""
    return Tag.objects.annotate(
        post_count=Count('posts', filter=Q(posts__status=Post.Status.PUBLISHED))
    ).filter(post_count__gt=0).order_by('-post_count')[:limit]


def search_posts(query=None, category=None, tag=None, date_from=None, date_to=None):
    """Search published posts"""
    posts = get_published_posts()
    
    if query:
        posts = posts.filter(
            Q(title__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(content__icontains=query)
        )
    if category:
        posts = posts.filter(category=category)
    if tag:
        posts = posts.filter(tags=tag)
    if date_from:
        posts = posts.filter(published_at__date__gte=date_from)
    if date_to:
        posts = posts.filter(published_at__date__lte=date_to)
    
    return posts


# ---------- Public views ----------
@require_GET
def post_list(request):
    """List view for blog posts"""
    posts = get_published_posts()
    
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'posts': page_obj,
        'categories': get_categories_with_counts(),
        'popular_tags': get_tags_with_counts(),
        'featured_posts': get_featured_posts(),
        'search_form': SearchForm(request.GET or None),
    }
    return render(request, 'blog/post_list.html', context)


@cache_page(60 * 15)
@require_GET
def post_detail(request, slug):
    """Detail view for a blog post"""
    post = get_object_or_404(get_published_posts(), slug=slug)
    
    # Increment view count
    post.view_count += 1
    post.save(update_fields=['view_count'])
    
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
        'comment_form': CommentForm(post=post, request=request),
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
        'posts': page_obj,
        'category': category,
        'categories': get_categories_with_counts(),
    }
    return render(request, 'blog/category_posts.html', context)


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
    }
    return render(request, 'blog/post_list.html', context)


@require_GET
def post_archive_year(request, year):
    """List posts by year"""
    posts = get_published_posts().filter(published_at__year=year)
    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {'posts': page_obj, 'year': year, 'title': f'Posts from {year}'}
    return render(request, 'blog/archive_year.html', context)


@require_GET
def post_archive_month(request, year, month):
    """List posts by year and month"""
    posts = get_published_posts().filter(published_at__year=year, published_at__month=month)
    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {'posts': page_obj, 'year': year, 'month': month, 'title': f'Posts from {year}/{month:02d}'}
    return render(request, 'blog/archive_month.html', context)


@require_POST
def search_posts(request):
    """Search blog posts (POST for form submission, but uses GET params)"""
    form = SearchForm(request.GET or None)
    posts = []
    if form.is_valid():
        posts = search_posts(
            query=form.cleaned_data.get('q'),
            category=form.cleaned_data.get('category'),
            tag=form.cleaned_data.get('tag'),
            date_from=form.cleaned_data.get('date_from'),
            date_to=form.cleaned_data.get('date_to'),
        )
    
    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {'form': form, 'page_obj': page_obj, 'query': request.GET.get('q', '')}
    return render(request, 'blog/search_results.html', context)


# ---------- Comment handling ----------
@require_POST
def add_comment(request, slug):
    """Submit a comment on a post"""
    post = get_object_or_404(Post, slug=slug, status=Post.Status.PUBLISHED)
    form = CommentForm(request.POST, post=post, request=request)
    
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
        messages.success(request, 'Comment submitted. It will appear after moderation.')
        return redirect(post.get_absolute_url())
    else:
        messages.error(request, 'Please correct the errors below.')
        return render(request, 'blog/post_detail.html', {
            'post': post,
            'comment_form': form,
            'recent_posts': get_recent_posts(exclude_post=post),
            'comments': post.comments.filter(status=Comment.Status.APPROVED),
            'social_share_urls': {},  # or compute if needed
        })


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
    notes = request.POST.get('notes', '')
    
    if action == 'approve':
        comment.status = Comment.Status.APPROVED
        comment.save()
        messages.success(request, 'Comment approved.')
    elif action == 'reject':
        comment.status = Comment.Status.REJECTED
        comment.save()
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
            ip_address=request.META.get('REMOTE_ADDR', ''),
        )
        
        post.share_count += 1
        post.save(update_fields=['share_count'])
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)