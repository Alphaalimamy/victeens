from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Child, ChildCategory, ChildStory, Need, Sponsorship, ChildPhoto
from .forms import ChildSponsorshipForm, ChildSearchForm

def children_list(request):
    """List all children available for sponsorship"""
    children = Child.objects.filter(
        is_published=True,
        status='active',
        sponsorship_needed=True
    ).select_related('case_manager').prefetch_related('categories', 'photos')
    
    # Filter by category if provided
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(ChildCategory, slug=category_slug, is_active=True)
        children = children.filter(categories=category)
    
    # Filter by age if provided
    min_age = request.GET.get('min_age')
    max_age = request.GET.get('max_age')
    if min_age:
        children = children.filter(age__gte=min_age)
    if max_age:
        children = children.filter(age__lte=max_age)
    
    # Search if provided
    search_query = request.GET.get('search')
    if search_query:
        children = children.filter(
            Q(code_name__icontains=search_query) |
            Q(background_summary__icontains=search_query) |
            Q(interests__icontains=search_query) |
            Q(career_aspirations__icontains=search_query)
        )
    
    # Sort
    sort_by = request.GET.get('sort', 'display_order')
    if sort_by == 'age':
        children = children.order_by('age')
    elif sort_by == 'newest':
        children = children.order_by('-date_admitted')
    elif sort_by == 'urgent':
        children = children.order_by('display_order', 'date_admitted')
    else:
        children = children.order_by('display_order', 'code_name')
    
    # Pagination
    paginator = Paginator(children, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories for filter
    categories = ChildCategory.objects.filter(is_active=True)
    
    context = {
        'title': 'Meet Our Teens',
        'page_obj': page_obj,
        'categories': categories,
        'search_form': ChildSearchForm(request.GET),
        'total_children': children.count(),
        'active_filters': {
            'category': category_slug,
            'min_age': min_age,
            'max_age': max_age,
            'search': search_query,
            'sort': sort_by,
        }
    }
    return render(request, 'children/list.html', context)


def child_detail(request, slug):
    """Child detail page"""
    child = get_object_or_404(Child, slug=slug, is_published=True)
    
    # Check if user can view private information
    can_view_private = request.user.is_authenticated and (
        request.user.is_staff_member or 
        Sponsorship.objects.filter(child=child, sponsor=request.user, status='active').exists()
    )
    
    # Get related data
    stories = ChildStory.objects.filter(
        child=child, 
        is_approved=True, 
        is_published=True
    ).order_by('-is_featured', '-created_at')[:5]
    
    needs = Need.objects.filter(
        child=child,
        is_public=True,
        status__in=['pending', 'funded', 'in_progress']
    ).order_by('priority', 'display_order')
    
    photos = ChildPhoto.objects.filter(
        child=child,
        is_approved=True,
        can_display_publicly=True
    ).order_by('display_order', '-created_at')
    
    # Check if user is already sponsoring this child
    is_sponsor = False
    if request.user.is_authenticated:
        is_sponsor = Sponsorship.objects.filter(
            child=child, 
            sponsor=request.user, 
            status='active'
        ).exists()
    
    context = {
        'title': child.code_name,
        'child': child,
        'stories': stories,
        'needs': needs,
        'photos': photos,
        'can_view_private': can_view_private,
        'is_sponsor': is_sponsor,
    }
    return render(request, 'children/detail.html', context)


def child_stories(request, slug):
    """List all stories for a child"""
    child = get_object_or_404(Child, slug=slug, is_published=True)
    stories = ChildStory.objects.filter(
        child=child, 
        is_approved=True, 
        is_published=True
    ).order_by('-created_at')
    
    paginator = Paginator(stories, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': f'Stories about {child.code_name}',
        'child': child,
        'page_obj': page_obj,
    }
    return render(request, 'children/stories.html', context)


def story_detail(request, slug):
    """Single story detail"""
    story = get_object_or_404(
        ChildStory, 
        slug=slug, 
        is_approved=True, 
        is_published=True,
        child__is_published=True
    )
    
    # Get related stories
    related_stories = ChildStory.objects.filter(
        child=story.child,
        is_approved=True,
        is_published=True
    ).exclude(pk=story.pk).order_by('-created_at')[:3]
    
    context = {
        'title': story.title,
        'story': story,
        'related_stories': related_stories,
    }
    return render(request, 'children/story_detail.html', context)


@login_required
def start_sponsorship(request, slug):
    """Start sponsorship process"""
    child = get_object_or_404(Child, slug=slug, is_published=True, sponsorship_needed=True)
    
    # Check if already sponsoring
    existing_sponsorship = Sponsorship.objects.filter(
        child=child, 
        sponsor=request.user,
        status__in=['active', 'pending']
    ).first()
    
    if existing_sponsorship:
        messages.info(request, f'You already have an active sponsorship request for {child.code_name}.')
        return redirect('children:detail', slug=slug)
    
    if request.method == 'POST':
        form = ChildSponsorshipForm(request.POST, child=child, user=request.user)
        if form.is_valid():
            sponsorship = form.save(commit=False)
            sponsorship.child = child
            sponsorship.sponsor = request.user
            sponsorship.status = 'pending'
            sponsorship.save()
            
            # Create initial donation record (simplified)
            # In production, this would integrate with payment system
            
            messages.success(
                request, 
                f'Your sponsorship application for {child.code_name} has been submitted! '
                f'Our team will review it and contact you within 48 hours.'
            )
            return redirect('children:sponsorship_confirmation', slug=slug)
    else:
        form = ChildSponsorshipForm(child=child, user=request.user)
    
    context = {
        'title': f'Sponsor {child.code_name}',
        'child': child,
        'form': form,
    }
    return render(request, 'children/start_sponsorship.html', context)


@login_required
def sponsorship_confirmation(request, slug):
    """Sponsorship confirmation page"""
    child = get_object_or_404(Child, slug=slug)
    
    # Get latest sponsorship for this child by this user
    sponsorship = Sponsorship.objects.filter(
        child=child, 
        sponsor=request.user
    ).order_by('-created_at').first()
    
    if not sponsorship:
        messages.error(request, 'No sponsorship application found.')
        return redirect('children:detail', slug=slug)
    
    context = {
        'title': 'Sponsorship Application Submitted',
        'child': child,
        'sponsorship': sponsorship,
    }
    return render(request, 'children/sponsorship_confirmation.html', context)


@login_required
def my_sponsorships(request):
    """User's active sponsorships"""
    sponsorships = Sponsorship.objects.filter(
        sponsor=request.user
    ).select_related('child').order_by('-created_at')
    
    active_sponsorships = sponsorships.filter(status='active')
    pending_sponsorships = sponsorships.filter(status='pending')
    past_sponsorships = sponsorships.filter(status__in=['cancelled', 'completed', 'paused'])
    
    context = {
        'title': 'My Sponsorships',
        'active_sponsorships': active_sponsorships,
        'pending_sponsorships': pending_sponsorships,
        'past_sponsorships': past_sponsorships,
    }
    return render(request, 'children/my_sponsorships.html', context)


@login_required
def sponsorship_detail(request, sponsorship_id):
    """Detailed view of a sponsorship"""
    sponsorship = get_object_or_404(
        Sponsorship, 
        id=sponsorship_id, 
        sponsor=request.user
    )
    
    # Get child updates for sponsors
    updates = sponsorship.child.updates.filter(
        is_approved=True,
        sent_to_sponsors=True
    ).order_by('-created_at')
    
    context = {
        'title': f'Sponsoring {sponsorship.child.code_name}',
        'sponsorship': sponsorship,
        'updates': updates,
    }
    return render(request, 'children/sponsorship_detail.html', context)


@login_required
@require_POST
def cancel_sponsorship(request, sponsorship_id):
    """Cancel a sponsorship"""
    sponsorship = get_object_or_404(
        Sponsorship, 
        id=sponsorship_id, 
        sponsor=request.user,
        status='active'
    )
    
    sponsorship.status = 'cancelled'
    sponsorship.save()
    
    messages.success(request, f'Your sponsorship for {sponsorship.child.code_name} has been cancelled.')
    return redirect('children:my_sponsorships')


def child_needs(request, slug):
    """List all needs for a child"""
    child = get_object_or_404(Child, slug=slug, is_published=True)
    needs = Need.objects.filter(
        child=child,
        is_public=True
    ).order_by('priority', 'display_order')
    
    context = {
        'title': f'Needs of {child.code_name}',
        'child': child,
        'needs': needs,
    }
    return render(request, 'children/needs.html', context)


def child_gallery(request, slug):
    """Photo gallery for a child"""
    child = get_object_or_404(Child, slug=slug, is_published=True)
    photos = ChildPhoto.objects.filter(
        child=child,
        is_approved=True,
        can_display_publicly=True
    ).order_by('display_order', '-created_at')
    
    # Group by photo type
    photos_by_type = {}
    for photo in photos:
        photos_by_type.setdefault(photo.get_photo_type_display(), []).append(photo)
    
    context = {
        'title': f'Photos of {child.code_name}',
        'child': child,
        'photos_by_type': photos_by_type,
    }
    return render(request, 'children/gallery.html', context)


def child_success_stories(request):
    """Success stories of graduated/reunited children"""
    children = Child.objects.filter(
        is_published=True,
        status__in=['graduated', 'reunited']
    ).order_by('-date_departed')
    
    # Get their success stories
    stories = ChildStory.objects.filter(
        child__in=children,
        story_type='success',
        is_approved=True,
        is_published=True
    ).select_related('child').order_by('-created_at')
    
    paginator = Paginator(stories, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': 'Success Stories',
        'page_obj': page_obj,
    }
    return render(request, 'children/success_stories.html', context)


@login_required
def send_message_to_child(request, child_id):
    """Send message to sponsored child (moderated)"""
    # This would be implemented in Week 3
    pass


def child_statistics(request):
    """Public statistics about children"""
    total_children = Child.objects.filter(is_published=True).count()
    active_children = Child.objects.filter(is_published=True, status='active').count()
    sponsored_children = Child.objects.filter(is_published=True, is_sponsored=True).count()
    graduated_children = Child.objects.filter(is_published=True, status='graduated').count()
    
    # Age distribution
    age_groups = {
        '13-15': Child.objects.filter(is_published=True, age__range=[13, 15]).count(),
        '16-18': Child.objects.filter(is_published=True, age__range=[16, 18]).count(),
        '19+': Child.objects.filter(is_published=True, age__gte=19).count(),
    }
    
    context = {
        'title': 'Child Statistics',
        'total_children': total_children,
        'active_children': active_children,
        'sponsored_children': sponsored_children,
        'graduated_children': graduated_children,
        'age_groups': age_groups,
    }
    return render(request, 'children/statistics.html', context)