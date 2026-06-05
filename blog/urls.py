from django.urls import path, re_path
from . import views

app_name = 'blog'

urlpatterns = [
    # Main blog views
    path('', views.post_list, name='blog'),
    path('search/', views.search_posts, name='search_posts'),
    path('post-detail/<slug:slug>/', views.post_detail, name='post_detail'),

    
    # Category and tag views
    path('category/<slug:slug>/',  views.category_post_list, name='category_post_list'),
    path('tag/<slug:slug>/',  views.tag_post_list,   name='tag_post_list'),
    
    path('track-share/', views.track_social_share, name='track_share'),
    
  
]