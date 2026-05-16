from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.cache import cache_page
from django.http import HttpResponseForbidden, JsonResponse, Http404
from django.db.models import Q
import json

from .models import Post, Category, Tag, Comment, SocialShare
from .forms import PostForm, CommentForm, CommentModerationForm, SearchForm
from .services import BlogService, CommentService, AnalyticsService


# Helper function to check if user is staff
def staff_required(function):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        return function(request, *args, **kwargs)
    return wrapper


# Helper function to check if user is author or staff
def author_or_staff_required(function, model_class=Post):
    def wrapper(request, *args, **kwargs):
        obj = get_object_or_404(model_class, **kwargs)
        if not (request.user == obj.author or request.user.is_staff):
            return HttpResponseForbidden()
        return function(request, *args, **kwargs)
    return wrapper


@require_GET
def post_list(request):
    """List view for blog posts"""
    posts = BlogService.get_published_posts()
    
    # Pagination
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'posts': page_obj,
        'categories': BlogService.get_categories_with_counts(),
        'popular_tags': BlogService.get_tags_with_counts(),
        'featured_posts': BlogService.get_featured_posts(),
        'search_form': SearchForm(request.GET or None),
    }
    
    return render(request, 'blog/post_list.html', context)


@cache_page(60 * 15)
@require_GET
def post_detail(request, slug):
    """Detail view for a blog post"""
    post = BlogService.get_post_by_slug(slug)
    
    if not post:
        raise Http404("Post not found")
    
    # Increment view count
    BlogService.increment_post_view(post, request)
    
    # Get related data - make sure to limit to 3 for related posts
    recent_posts = BlogService.get_recent_posts(limit=3, exclude_post=post)
    comments = BlogService.get_approved_comments(post)
    
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
        'recent_posts': recent_posts,  # This will be available in template
        'comments': comments,
        'comment_form': CommentForm(post=post, request=request),
        'social_share_urls': social_share_urls,
    }
    
    return render(request, 'blog/post_detail.html', context)


# blog/views.py
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

@csrf_exempt
def track_share(request):
    """Track social media shares"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            post_id = data.get('post_id')
            platform = data.get('platform')
            
            # Get the post
            try:
                post = Post.objects.get(id=post_id)
            except Post.DoesNotExist:
                return JsonResponse({'error': 'Post not found'}, status=404)
            
            # Create SocialShare record
            SocialShare.objects.create(
                post=post,
                platform=platform,
                shared_by=request.user if request.user.is_authenticated else None,
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
            
            # Increment share count
            post.share_count += 1
            post.save(update_fields=['share_count'])
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@require_GET
def category_post_list(request, slug):
    """List posts by category"""
    category = get_object_or_404(Category, slug=slug)
    posts = BlogService.get_published_posts().filter(category=category)
    
    # Pagination
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'posts': page_obj,
        'category': category,
        'categories': BlogService.get_categories_with_counts(),
    }
    
    return render(request, 'blog/category_posts.html', context)



def tag_post_list(request, slug):
    """View for listing posts with a specific tag"""
    tag = get_object_or_404(Tag, slug=slug)
    
    # Get published posts with this tag
    posts_list = BlogService.get_published_posts().filter(tags=tag).order_by('-published_date')
    
    # Pagination
    paginator = Paginator(posts_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get context data
    context = {
        'tag': tag,
        'page_obj': page_obj,
        'categories': BlogService.get_categories_with_counts(),
        'popular_tags': BlogService.get_tags_with_counts(),
        'query': '',
    }
    
    # Use the post_list.html template
    return render(request, 'blog/post_list.html', context)



@login_required
def post_create(request):
    """Create a new blog post"""
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, 'Post created successfully!')
            return redirect('blog:post_detail', 
                          year=post.publish.year,
                          month=post.publish.month,
                          day=post.publish.day,
                          slug=post.slug)
    else:
        form = PostForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Create New Post'
    }
    
    return render(request, 'blog/post_form.html', context)


@login_required
def post_update(request, slug):
    """Update an existing blog post"""
    post = get_object_or_404(Post, slug=slug)
    
    # Check permissions
    if not (request.user == post.author or request.user.is_staff):
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post, user=request.user)
        if form.is_valid():
            post = form.save()
            messages.success(request, 'Post updated successfully!')
            return redirect('blog:post_detail', 
                          year=post.publish.year,
                          month=post.publish.month,
                          day=post.publish.day,
                          slug=post.slug)
    else:
        form = PostForm(instance=post, user=request.user)
    
    context = {
        'form': form,
        'post': post,
        'title': 'Update Post'
    }
    
    return render(request, 'blog/post_form.html', context)


@login_required
def post_delete(request, slug):
    """Delete a blog post"""
    post = get_object_or_404(Post, slug=slug)
    
    # Check permissions
    if not (request.user == post.author or request.user.is_staff):
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully!')
        return redirect('blog:post_list')
    
    context = {
        'post': post,
        'title': 'Delete Post'
    }
    
    return render(request, 'blog/post_confirm_delete.html', context)


@login_required
@staff_required
def comment_moderation_list(request):
    """View for moderating comments"""
    comments = CommentService.get_pending_comments()
    
    context = {
        'comments': comments,
        'title': 'Comment Moderation'
    }
    
    return render(request, 'blog/comment_moderation.html', context)


@require_POST
def search_posts(request):
    """Search blog posts"""
    form = SearchForm(request.GET or None)
    posts = []
    
    if form.is_valid():
        posts = BlogService.search_posts(
            query=form.cleaned_data.get('q'),
            category=form.cleaned_data.get('category'),
            tag=form.cleaned_data.get('tag'),
            date_from=form.cleaned_data.get('date_from'),
            date_to=form.cleaned_data.get('date_to'),
        )
    
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'query': request.GET.get('q', ''),
        'title': 'Search Results'
    }
    
    return render(request, 'blog/search_results.html', context)


@login_required
def blog_dashboard(request):
    """Blog dashboard for authors"""
    user = request.user
    
    if user.is_staff:
        posts = Post.objects.filter(author=user)
        total_views = sum(post.view_count for post in posts)
        total_comments = Comment.objects.filter(post__author=user).count()
    else:
        posts = Post.objects.filter(author=user)
        total_views = 0
        total_comments = 0
    
    context = {
        'posts': posts,
        'total_views': total_views,
        'total_comments': total_comments,
        'title': 'Blog Dashboard'
    }
    
    return render(request, 'blog/dashboard.html', context)




@require_POST
def add_comment(request, slug):
    """Handle comment submission"""
    post = get_object_or_404(Post, slug=slug, status=Post.Status.PUBLISHED)
    
    comment, form = CommentService.create_comment(post, request.POST, request)
    
    if comment:
        messages.success(request, 'Comment submitted successfully! It will appear after moderation.')
        return redirect(post.get_absolute_url())
    else:
        messages.error(request, 'Please correct the errors below.')
        return render(request, 'blog/post_detail.html', {
            'post': post,
            'comment_form': form,
            'recent_posts': BlogService.get_recent_posts(exclude_post=post),
            'comments': BlogService.get_approved_comments(post),
        })


@require_POST
@login_required
@staff_required
def moderate_comment(request, comment_id):
    """Handle comment moderation"""
    comment = get_object_or_404(Comment, id=comment_id)
    action = request.POST.get('action')
    notes = request.POST.get('notes', '')
    
    CommentService.moderate_comment(comment, action, request.user, notes)
    
    messages.success(request, f'Comment {action}d successfully!')
    return redirect('blog:comment_moderation')


@require_POST
def track_social_share(request):
    """Track social media shares"""
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
        
        # Increment share count
        post.share_count += 1
        post.save(update_fields=['share_count'])
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# Optional: Archive views by year/month
@require_GET
def post_archive_year(request, year):
    """List posts by year"""
    posts = BlogService.get_published_posts().filter(publish__year=year)
    
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'posts': page_obj,
        'year': year,
        'title': f'Posts from {year}'
    }
    
    return render(request, 'blog/archive_year.html', context)


@require_GET
def post_archive_month(request, year, month):
    """List posts by year and month"""
    posts = BlogService.get_published_posts().filter(publish__year=year, publish__month=month)
    
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'posts': page_obj,
        'year': year,
        'month': month,
        'title': f'Posts from {year}/{month:02d}'
    }
    
    return render(request, 'blog/archive_month.html', context)