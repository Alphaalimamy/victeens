from django.urls import path, re_path
from . import views

app_name = 'blog'

urlpatterns = [
    # Main blog views
    path('', views.post_list, name='blog'),
    path('create/', views.post_create, name='post_create'),
    path('dashboard/', views.blog_dashboard, name='dashboard'),
    path('search/', views.search_posts, name='search_posts'),
    
    # Post detail (alternative without dates)
    path('post/<int:year>/<int:month>/<int:day>/<slug:slug>/', views.post_detail, name='post_detail'),
    
    # Post CRUD
    path('post/<slug:slug>/edit/', views.post_update, name='post_update'),
    path('post/<slug:slug>/delete/', views.post_delete, name='post_delete'),
    
    # Category and tag views
    path('category/<slug:slug>/',  views.category_post_list, name='category_post_list'),
    path('tag/<slug:slug>/',  views.tag_post_list,   name='tag_post_list'),
    
    path('track-share/', views.track_social_share, name='track_share'),
    
  
]