from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

from .forms import ContactForm
from .models import (
    ImpactStat, Testimonial, FAQ, Program, TeamMember,
    OrganizationProfile, CoreValue, Milestone, SiteConfiguration
)

def home_view(request):
    """Homepage view with dynamic hero content from SiteConfiguration"""
    config = SiteConfiguration.objects.first()  # Singleton – may be None if not created yet
    impact_stats = ImpactStat.objects.filter(is_active=True).order_by('order')[:4]
    testimonials = Testimonial.objects.filter(is_active=True).order_by('order', '-created_at')[:3]
    programs = Program.objects.filter(is_active=True).order_by('order', '-created_at')[:3]
    
    context = {
        'title': 'Home',
        'config': config,
        'impact_stats': impact_stats,
        'testimonials': testimonials,
        'programs': programs,
        'featured': True,
    }
    return render(request, 'core/home.html', context)


def about_view(request):
    """About page view"""
    context = {
        "title": "About Us",
        "team_members": TeamMember.objects.filter(is_active=True).order_by('order'),
        "profile": OrganizationProfile.objects.first(),
        "values": CoreValue.objects.all().order_by('order'),
        "milestones": Milestone.objects.all().order_by('order', 'year'),
        "general_faqs": FAQ.objects.filter(category="general", is_active=True).order_by('order'),
        "donation_faqs": FAQ.objects.filter(category="donation", is_active=True).order_by('order'),
        "volunteer_faqs": FAQ.objects.filter(category="volunteer", is_active=True).order_by('order'),
    }
    return render(request, 'core/about.html', context)


def programs_view(request):
    """Programs listing page"""
    programs = Program.objects.filter(is_active=True).order_by('order', 'title')
    context = {'programs': programs}
    return render(request, 'core/programs.html', context)


def volunteer_view(request):
    """Volunteer application page"""
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        interests = request.POST.getlist('interests')
        availability = request.POST.get('availability')
        message = request.POST.get('message')
        
        # Optional: Save to Volunteer model (create one if needed)
        # from .models import Volunteer
        # Volunteer.objects.create(
        #     first_name=first_name, last_name=last_name, email=email,
        #     phone=phone, interests=', '.join(interests),
        #     availability=availability, message=message
        # )
        
        # Email to admin
        subject = f'New Volunteer Application: {first_name} {last_name}'
        body = f"""
New Volunteer Application Received:

Name: {first_name} {last_name}
Email: {email}
Phone: {phone}
Interests: {', '.join(interests)}
Availability: {availability}
Message: {message}
        """
        send_mail(
            subject, body,
            'noreply@victoryteens.org',
            ['admin@victoryteens.org'],
            fail_silently=False,
        )
        
        # Confirmation email to volunteer
        confirmation_body = f"""
Dear {first_name},

Thank you for your interest in volunteering with Victory Teens Organization!
We have received your application and will review it shortly.

Our team will contact you within 3-5 business days to discuss next steps.

Best regards,
Victory Teens Organization Team
        """
        send_mail(
            'Thank You for Your Volunteer Application',
            confirmation_body,
            'noreply@victoryteens.org',
            [email],
            fail_silently=False,
        )
        
        messages.success(request, 'Thank you for your application! We will contact you soon.')
        return redirect('volunteer_thank_you')
    
    return render(request, 'core/volunteer.html')


def contact_view(request):
    """Contact page with form handling"""
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
                        f"IP Address: {contact.ip_address}"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.CONTACT_EMAIL],
                    fail_silently=True,
                )
            except Exception as exc:
                # In production, replace with proper logging
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
    }
    return render(request, "core/contact.html", context)