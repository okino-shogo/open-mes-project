"""
Custom template tags for static files handling
Provides fallback for md5url when not available (e.g., Vercel deployment)
"""
from django import template
from django.templatetags.static import static
from django.conf import settings

register = template.Library()

@register.simple_tag
def smart_static(path):
    """
    Smart static file handler that uses md5url if available,
    otherwise falls back to regular static tag
    """
    # Check if we're in Vercel environment or md5url is not available
    if getattr(settings, 'IS_VERCEL', False):
        return static(path)
    
    # Try to use md5url if available
    try:
        from django_static_md5url.templatetags.md5url import md5url
        return md5url(path)
    except (ImportError, ModuleNotFoundError):
        # Fallback to regular static if md5url is not available
        return static(path)

# Alias for backward compatibility
@register.simple_tag  
def md5url(path):
    """
    Alias for smart_static to maintain compatibility with existing templates
    """
    return smart_static(path) 