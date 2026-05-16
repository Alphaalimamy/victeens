from django.urls import path
from . import views

app_name = 'children'

urlpatterns = [
    # Child listings
    path('', views.children_list, name='list'),
    path('success-stories/', views.child_success_stories, name='success_stories'),
    path('statistics/', views.child_statistics, name='statistics'),
    
    # Individual child
    path('<slug:slug>/', views.child_detail, name='detail'),
    path('<slug:slug>/stories/', views.child_stories, name='stories'),
    path('<slug:slug>/stories/<slug:story_slug>/', views.story_detail, name='story_detail'),
    path('<slug:slug>/needs/', views.child_needs, name='needs'),
    path('<slug:slug>/gallery/', views.child_gallery, name='gallery'),
    
    # Sponsorship
    path('<slug:slug>/sponsor/', views.start_sponsorship, name='start_sponsorship'),
    path('<slug:slug>/sponsor/confirm/', views.sponsorship_confirmation, name='sponsorship_confirmation'),
    
    # User sponsorship management
    path('my-sponsorships/', views.my_sponsorships, name='my_sponsorships'),
    path('sponsorship/<int:sponsorship_id>/', views.sponsorship_detail, name='sponsorship_detail'),
    path('sponsorship/<int:sponsorship_id>/cancel/', views.cancel_sponsorship, name='cancel_sponsorship'),
]