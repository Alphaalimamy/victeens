from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Post, Category, Tag, Comment
from .services import BlogService

User = get_user_model()


class BlogModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.tag = Tag.objects.create(
            name='Test Tag',
            slug='test-tag'
        )
    
    def test_post_creation(self):
        post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            author=self.user,
            content='Test content',
            category=self.category,
            status=Post.Status.PUBLISHED,
            published_date=timezone.now()
        )
        post.tags.add(self.tag)
        
        self.assertEqual(post.title, 'Test Post')
        self.assertEqual(post.author, self.user)
        self.assertTrue(post.is_published)
        self.assertEqual(post.reading_time, '1 min read')
    
    def test_category_str(self):
        self.assertEqual(str(self.category), 'Test Category')
    
    def test_tag_str(self):
        self.assertEqual(str(self.tag), 'Test Tag')


class BlogViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        # Create published post
        self.post = Post.objects.create(
            title='Test Published Post',
            slug='test-published-post',
            author=self.user,
            content='Test content for published post.',
            category=self.category,
            status=Post.Status.PUBLISHED,
            published_date=timezone.now()
        )
    
    def test_post_list_view(self):
        response = self.client.get(reverse('blog:post_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post_list.html')
        self.assertContains(response, 'Test Published Post')
    
    def test_post_detail_view(self):
        response = self.client.get(self.post.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post_detail.html')
        self.assertContains(response, 'Test Published Post')
    
    def test_category_view(self):
        response = self.client.get(
            reverse('blog:category_detail', kwargs={'slug': self.category.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/category_posts.html')


class BlogServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        # Create multiple posts
        for i in range(5):
            Post.objects.create(
                title=f'Test Post {i}',
                slug=f'test-post-{i}',
                author=self.user,
                content='Test content',
                category=self.category,
                status=Post.Status.PUBLISHED,
                published_date=timezone.now(),
                is_featured=(i < 2)  # First two are featured
            )
    
    def test_get_published_posts(self):
        posts = BlogService.get_published_posts()
        self.assertEqual(posts.count(), 5)
    
    def test_get_featured_posts(self):
        featured_posts = BlogService.get_featured_posts()
        self.assertEqual(featured_posts.count(), 2)
    
    def test_get_categories_with_counts(self):
        categories = BlogService.get_categories_with_counts()
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0].post_count, 5)


class CommentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            author=self.user,
            content='Test content',
            category=self.category,
            status=Post.Status.PUBLISHED,
            published_date=timezone.now(),
            allow_comments=True
        )
    
    def test_comment_creation(self):
        comment = Comment.objects.create(
            post=self.post,
            name='Test Commenter',
            email='commenter@example.com',
            content='Test comment content',
            status=Comment.Status.APPROVED
        )
        
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.name, 'Test Commenter')
        self.assertTrue(comment.status, Comment.Status.APPROVED)
    
    def test_comment_approval(self):
        comment = Comment.objects.create(
            post=self.post,
            name='Test Commenter',
            email='commenter@example.com',
            content='Test comment content',
            status=Comment.Status.PENDING
        )
        
        comment.approve(self.user)
        self.assertEqual(comment.status, Comment.Status.APPROVED)
        self.assertEqual(comment.moderated_by, self.user)