from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone

from .forms import ContactForm
from .models import (
    SiteConfiguration, SiteSettings, ImpactStat, Testimonial, Program,
    FAQ, TeamMember, OrganizationProfiles, CoreValue, Milestone,
    FocusArea, Impact, Partner, NewsletterSubscriber, Page, Teen
)

def home_view(request):
    """Homepage with all dynamic content from database"""
    config = SiteConfiguration.objects.first()
    settings_obj = SiteSettings.load()
    
    # Get all dynamic content
    impact_stats = ImpactStat.objects.filter(is_active=True).order_by('order')[:4]
    testimonials = Testimonial.objects.filter(is_active=True).order_by('order', '-created_at')[:3]
    programs = Program.objects.filter(is_active=True).order_by('order', '-created_at')[:3]
    featured_partners = Partner.objects.filter(is_active=True, featured=True).order_by('order')[:6]
    featured_teens = Teen.objects.filter(is_featured=True)[:4]
    
    context = {
        'config': config,
        'settings': settings_obj,
        'impact_stats': impact_stats,
        'testimonials': testimonials,
        'programs': programs,
        'featured_partners': featured_partners,
        'featured_teens': featured_teens,
        'title': 'Home',
    }
    return render(request, 'core/home.html', context)

def about_view(request):
    """About page with all dynamic content from database"""
    # Get all data from database - nothing hardcoded!
    profile = OrganizationProfiles.objects.first()
    values = CoreValue.objects.filter(is_active=True).order_by('order')
    focus_areas = FocusArea.objects.filter(is_active=True).order_by('order')
    milestones = Milestone.objects.all().order_by('order', 'year')
    team_members = TeamMember.objects.filter(is_active=True).order_by('order')
    impacts = Impact.objects.filter(is_active=True).order_by('order')
    partners = Partner.objects.filter(is_active=True).order_by('order')[:8]
    
    # Get FAQs by category
    general_faqs = FAQ.objects.filter(category="general", is_active=True).order_by('order')
    donation_faqs = FAQ.objects.filter(category="donation", is_active=True).order_by('order')
    volunteer_faqs = FAQ.objects.filter(category="volunteer", is_active=True).order_by('order')
    child_faqs = FAQ.objects.filter(category="child", is_active=True).order_by('order')
    
    context = {
        "title": "About Us",
        "profile": profile,
        "values": values,
        "focus_areas": focus_areas,
        "milestones": milestones,
        "team_members": team_members,
        "impacts": impacts,
        "partners": partners,
        "general_faqs": general_faqs,
        "donation_faqs": donation_faqs,
        "volunteer_faqs": volunteer_faqs,
        "child_faqs": child_faqs,
    }
    return render(request, 'core/about.html', context)

def team_member_detail(request, member_id):
    """Detailed view for a specific team member"""
    member = get_object_or_404(TeamMember, id=member_id, is_active=True)

    other_members = TeamMember.objects.filter(is_active=True).exclude(id=member.id).order_by('order')[:3]
    related_members = TeamMember.objects.filter(role=member.role,is_active=True).exclude(id=member.id).order_by('order')[:2]
    
    context = {
        'member': member,
        'other_members': other_members,
        'related_members': related_members,
        'title': f'{member.name} - Team Member',
    }
    return render(request, 'core/team_member_detail.html', context)

def programs_view(request):
    """Programs listing page - dynamic from database"""
    programs_list = Program.objects.filter(is_active=True).order_by('order', 'title')
    
    # Pagination
    paginator = Paginator(programs_list, 6)
    page_number = request.GET.get('page')
    programs = paginator.get_page(page_number)
    
    context = {
        'programs': programs,
        'title': 'Our Programs',
        'total_programs': programs_list.count(),
    }
    return render(request, 'core/programs.html', context)

def program_detail_view(request, slug):
    """Program detail page"""
    program = get_object_or_404(Program, slug=slug, is_active=True)
    
    # Get related programs (same category or just other active programs)
    related_programs = Program.objects.filter(is_active=True).exclude(id=program.id)[:3]
    
    context = {
        'program': program,
        'related_programs': related_programs,
        'title': program.title,
    }
    return render(request, 'core/program_detail.html', context)

def volunteer_view(request):
    """Volunteer page with dynamic content"""
    if request.method == 'POST':
        # Get form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        interests = request.POST.getlist('interests')
        availability = request.POST.get('availability')
        message = request.POST.get('message')
        
        # Email to admin
        settings_obj = SiteSettings.load()
        admin_email = settings_obj.contact_email
        
        send_mail(
            subject=f'New Volunteer Application: {first_name} {last_name}',
            message=f"""
New Volunteer Application Received:

Name: {first_name} {last_name}
Email: {email}
Phone: {phone}
Interests: {', '.join(interests)}
Availability: {availability}

Message:
{message}

IP Address: {request.META.get("REMOTE_ADDR")}
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            fail_silently=False,
        )
        
        # Confirmation email to volunteer
        send_mail(
            subject='Thank You for Your Volunteer Application',
            message=f"""
Dear {first_name},

Thank you for your interest in volunteering with Victory Teens Organization!
We have received your application and will review it shortly.

Our team will contact you within 3-5 business days to discuss next steps.

Best regards,
Victory Teens Organization Team
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        
        messages.success(request, 'Thank you for your application! We will contact you soon.')
        return redirect('volunteer_thank_you')
    
    # Get dynamic content for volunteer page
    current_volunteers = TeamMember.objects.filter(
        role='volunteer', is_active=True
    ).order_by('order')[:6]
    
    volunteer_faqs = FAQ.objects.filter(category="volunteer", is_active=True).order_by('order')
    
    context = {
        'title': 'Volunteer With Us',
        'current_volunteers': current_volunteers,
        'volunteer_faqs': volunteer_faqs,
        'volunteer_stats': {
            'total_volunteers': TeamMember.objects.filter(role='volunteer').count(),
            'active_countries': 15,
            'hours_contributed': '25,000+',
        }
    }
    return render(request, 'core/volunteer.html', context)

def volunteer_thank_you_view(request):
    """Success page after volunteer application"""
    context = {'title': 'Application Received'}
    return render(request, 'core/volunteer_success.html', context)

def contact_view(request):
    """Contact page with dynamic information from database"""
    settings_obj = SiteSettings.load()
    
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.ip_address = request.META.get("REMOTE_ADDR")
            contact.user_agent = request.META.get("HTTP_USER_AGENT", "")
            contact.save()

            # Send email notification
            try:
                send_mail(
                    subject=f"Victory Teens: New Contact - {contact.subject}",
                    message=(
                        f"Name: {contact.name}\n"
                        f"Email: {contact.email}\n"
                        f"Phone: {contact.phone or 'Not provided'}\n"
                        f"Subject: {contact.subject}\n\n"
                        f"Message:\n{contact.message}\n\n"
                        f"---\n"
                        f"IP Address: {contact.ip_address}\n"
                        f"User Agent: {contact.user_agent}"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings_obj.contact_email],
                    fail_silently=True,
                )
            except Exception as exc:
                print(f"Email sending failed: {exc}")

            messages.success(
                request,
                "Thank you for your message! We will get back to you within 24 hours.",
            )
            return redirect("contact")
    else:
        form = ContactForm()

    context = {
        "title": "Contact Us",
        "form": form,
        "settings": settings_obj,
    }
    return render(request, "core/contact.html", context)

def page_detail_view(request, slug):
    """Dynamic page view for any custom page"""
    page = get_object_or_404(Page, slug=slug, is_published=True)
    
    context = {
        'page': page,
        'title': page.title,
    }
    return render(request, 'core/page_detail.html', context)

def newsletter_subscribe(request):
    """Handle newsletter subscription"""
    if request.method == 'POST':
        email = request.POST.get('email')
        name = request.POST.get('name', '')
        
        if email:
            subscriber, created = NewsletterSubscriber.objects.get_or_create(
                email=email,
                defaults={'name': name}
            )
            
            if created:
                messages.success(request, 'Successfully subscribed to our newsletter!')
            else:
                messages.info(request, 'You are already subscribed to our newsletter.')
        else:
            messages.error(request, 'Please provide a valid email address.')
        
        return redirect(request.META.get('HTTP_REFERER', 'home'))
    
    return redirect('home')

def search_view(request):
    """Global search across multiple models"""
    query = request.GET.get('q', '')
    results = {}
    
    if query:
        results['programs'] = Program.objects.filter(
            title__icontains=query, is_active=True
        )
        results['team_members'] = TeamMember.objects.filter(
            name__icontains=query, is_active=True
        )
        results['faqs'] = FAQ.objects.filter(
            question__icontains=query, is_active=True
        )
        results['focus_areas'] = FocusArea.objects.filter(
            title__icontains=query, is_active=True
        )
        results['pages'] = Page.objects.filter(
            title__icontains=query, is_published=True
        )
    
    context = {
        'query': query,
        'results': results,
        'title': f'Search: {query}' if query else 'Search',
        'total_results': sum(len(v) for v in results.values()),
    }
    return render(request, 'core/search_results.html', context)

# API endpoints for AJAX loading
def api_core_values(request):
    values = CoreValue.objects.filter(is_active=True).values('title', 'icon', 'description')
    return JsonResponse({'status': 'success', 'data': list(values)})

def api_focus_areas(request):
    areas = FocusArea.objects.filter(is_active=True).values('title', 'icon', 'description')
    return JsonResponse({'status': 'success', 'data': list(areas)})

def api_team_members(request):
    members = TeamMember.objects.filter(is_active=True).values('name', 'role', 'title', 'bio')
    return JsonResponse({'status': 'success', 'data': list(members)})