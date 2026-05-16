from .models import SiteSettings

def site_settings(request):
    """Add site settings to all templates"""
    return {
        'site_settings': SiteSettings.load(),
        'site_name': SiteSettings.load().site_name,
        'contact_email': SiteSettings.load().contact_email,
    }