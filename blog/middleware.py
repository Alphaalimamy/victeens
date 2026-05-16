from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import ObjectDoesNotExist
from .models import Post
import re


class BlogViewTrackingMiddleware(MiddlewareMixin):
    """Middleware to track blog post views"""
    
    def process_response(self, request, response):
        # Only track successful GET requests
        if response.status_code == 200 and request.method == 'GET':
            # Check if this is a blog post detail page
            path = request.path
            blog_pattern = r'^/blog/\d{4}/\d{2}/\d{2}/[-\w]+/$|^/blog/[-\w]+/$'
            
            if re.match(blog_pattern, path):
                try:
                    # Extract slug from URL
                    slug = path.strip('/').split('/')[-1]
                    
                    # Try to get the post
                    post = Post.objects.get(slug=slug, status=Post.Status.PUBLISHED)
                    
                    # Track the view
                    from .services import BlogService
                    BlogService.increment_post_view(post, request)
                    
                except (Post.DoesNotExist, ValueError, IndexError):
                    pass
        
        return response