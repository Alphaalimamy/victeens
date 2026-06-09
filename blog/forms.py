from django import forms
from django.contrib.auth import get_user_model
from .models import Post, Comment, Category, Tag
from ckeditor.widgets import CKEditorWidget
from django.core.exceptions import ValidationError
import re

User = get_user_model()

class RichTextEditorWidget(CKEditorWidget):
    class Media:
        css = {'all': ('css/ckeditor-custom.css',)}

class PostForm(forms.ModelForm):
    content = forms.CharField(widget=RichTextEditorWidget(config_name='default'))
    tags_input = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Tags separated by commas'}))
    
    class Meta:
        model = Post
        fields = [
            'title', 'excerpt', 'content', 'category',
            'hero_image', 'hero_caption', 'video_url',
            'seo_title', 'meta_description', 'og_image',
            'status', 'published_at', 'is_featured', 'allow_comments'
        ]
        widgets = {
            'excerpt': forms.Textarea(attrs={'rows': 3}),
            'meta_description': forms.Textarea(attrs={'rows': 2}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'published_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['tags_input'].initial = ', '.join(tag.name for tag in self.instance.tags.all())
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 10:
            raise ValidationError("Title must be at least 10 characters.")
        return title
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if len(content) < 100:
            raise ValidationError("Content must be at least 100 characters.")
        # spam check
        spam_patterns = [r'buy now', r'click here', r'viagra', r'casino']
        for pattern in spam_patterns:
            if len(re.findall(pattern, content, re.IGNORECASE)) > 3:
                raise ValidationError("Content appears spammy.")
        return content
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.author = self.user
        if commit:
            instance.save()
            tags_input = self.cleaned_data.get('tags_input', '')
            if tags_input:
                tag_names = [name.strip() for name in tags_input.split(',') if name.strip()]
                tags = []
                for tag_name in tag_names:
                    tag, _ = Tag.objects.get_or_create(name=tag_name, defaults={'slug': tag_name.lower().replace(' ', '-')})
                    tags.append(tag)
                instance.tags.set(tags)
        return instance

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['name', 'content', 'parent']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Share your thoughts...'}),
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}),
            'parent': forms.HiddenInput(),
        }
    

    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if len(content) < 10:
            raise ValidationError("Comment too short.")
        if len(content) > 1000:
            raise ValidationError("Comment too long.")
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
    class Meta:
        model = Comment
        fields = ['status', 'moderation_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'moderation_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-textarea'}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

class SearchForm(forms.Form):
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Search...'}))
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False, empty_label="All Categories")
    tag = forms.ModelChoiceField(queryset=Tag.objects.all(), required=False, empty_label="All Tags")
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))