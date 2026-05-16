from django import forms
from django.contrib.auth import get_user_model
from .models import Post, Comment, Category, Tag
from ckeditor.widgets import CKEditorWidget
from django.core.exceptions import ValidationError
import re

User = get_user_model()


class RichTextEditorWidget(CKEditorWidget):
    """Custom CKEditor widget with our configuration"""
    class Media:
        css = {
            'all': ('css/ckeditor-custom.css',)
        }


class PostForm(forms.ModelForm):
    """Form for creating/editing blog posts"""
    content = forms.CharField(widget=RichTextEditorWidget(config_name='default'))
    tags_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Add tags separated by commas',
            'class': 'tag-input'
        }),
        help_text="Enter tags separated by commas"
    )
    
    class Meta:
        model = Post
        fields = [
            'title', 'excerpt', 'content', 'category', 
            'featured_image', 'thumbnail_image', 'status',
            'post_type', 'is_featured', 'allow_comments',
            'meta_title', 'meta_description'
        ]
        widgets = {
            'excerpt': forms.Textarea(attrs={'rows': 3}),
            'meta_description': forms.Textarea(attrs={'rows': 2}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'post_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk:
            self.fields['tags_input'].initial = ', '.join(tag.name for tag in self.instance.tags.all())
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 10:
            raise ValidationError("Title must be at least 10 characters long.")
        return title
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        # Basic content validation
        if len(content) < 100:
            raise ValidationError("Content must be at least 100 characters long.")
        
        # Check for spam patterns (basic example)
        spam_patterns = [
            r'buy now', r'click here', r'viagra', r'casino',
            r'http://', r'https://',  # Multiple links
        ]
        
        for pattern in spam_patterns:
            if len(re.findall(pattern, content, re.IGNORECASE)) > 3:
                raise ValidationError("Content appears to contain spam-like patterns.")
        
        return content
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.user:
            instance.author = self.user
        
        if commit:
            instance.save()
            
            # Handle tags
            tags_input = self.cleaned_data.get('tags_input', '')
            if tags_input:
                tag_names = [name.strip() for name in tags_input.split(',') if name.strip()]
                tags = []
                for tag_name in tag_names:
                    tag, created = Tag.objects.get_or_create(
                        name=tag_name,
                        defaults={'slug': tag_name.lower().replace(' ', '-')}
                    )
                    tags.append(tag)
                instance.tags.set(tags)
        
        return instance


class CommentForm(forms.ModelForm):
    """Form for submitting comments"""
    class Meta:
        model = Comment
        fields = ['name', 'email', 'website', 'content', 'parent']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Share your thoughts...',
                'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-vto-orange focus:border-transparent'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-vto-orange focus:border-transparent'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-vto-orange focus:border-transparent'
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-vto-orange focus:border-transparent'
            }),
            'parent': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        self.post = kwargs.pop('post', None)
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        if self.request and self.request.user.is_authenticated:
            self.fields['name'].initial = self.request.user.get_full_name() or self.request.user.username
            self.fields['email'].initial = self.request.user.email
            self.fields['name'].widget.attrs['readonly'] = True
            self.fields['email'].widget.attrs['readonly'] = True
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if len(content) < 10:
            raise ValidationError("Comment must be at least 10 characters long.")
        if len(content) > 1000:
            raise ValidationError("Comment must not exceed 1000 characters.")
        return content
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.post:
            instance.post = self.post
        
        if self.request:
            instance.ip_address = self.request.META.get('REMOTE_ADDR')
            instance.user_agent = self.request.META.get('HTTP_USER_AGENT', '')
            
            if self.request.user.is_authenticated:
                instance.user = self.request.user
        
        if commit:
            instance.save()
        
        return instance


class CommentModerationForm(forms.ModelForm):
    """Form for moderating comments (admin only)"""
    class Meta:
        model = Comment
        fields = ['status', 'moderation_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'moderation_notes': forms.Textarea(attrs={'rows': 3}),
        }


class CategoryForm(forms.ModelForm):
    """Form for creating/editing categories"""
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class SearchForm(forms.Form):
    """Form for searching blog posts"""
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search articles...',
            'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-vto-orange focus:border-transparent'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    tag = forms.ModelChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        empty_label="All Tags",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'})
    )