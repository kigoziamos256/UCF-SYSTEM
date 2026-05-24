from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def profile_picture(user, size=40, css_class=""):
    """Generate profile picture HTML tag"""
    if not user or not user.is_authenticated:
        return mark_safe(f'<div class="profile-placeholder {css_class}" style="width:{size}px;height:{size}px;border-radius:50%;background:#6c757d;"></div>')
    
    try:
        if hasattr(user, 'member') and user.member.profile_picture and user.member.profile_picture.name:
            img_url = user.member.profile_picture.url
        else:
            # Generate initials avatar
            initials = get_initials(user)
            img_url = f"https://ui-avatars.com/api/?name={initials}&size={size}&background=0D6EFD&color=fff&length=2&font-size=0.5"
    except:
        initials = user.username[:2].upper()
        img_url = f"https://ui-avatars.com/api/?name={initials}&size={size}&background=0D6EFD&color=fff&length=2&font-size=0.5"
    
    return mark_safe(
        f'<img src="{img_url}" '
        f'alt="{user.username}" '
        f'class="profile-picture {css_class}" '
        f'style="width: {size}px; height: {size}px; object-fit: cover; border-radius: 50%; border: 2px solid #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">'
    )

@register.simple_tag
def profile_picture_with_name(user, size=40, show_name=True):
    """Generate profile picture with name"""
    if not user:
        return ''
    
    html = '<div class="d-flex align-items-center">'
    html += str(profile_picture(user, size, 'me-2'))
    
    if show_name:
        full_name = user.get_full_name() or user.username
        html += f'<span class="profile-name">{full_name}</span>'
    
    html += '</div>'
    return mark_safe(html)

def get_initials(user):
    """Get user initials for avatar"""
    full_name = user.get_full_name()
    if full_name:
        name_parts = full_name.split()
        if len(name_parts) >= 2:
            return f"{name_parts[0][0]}{name_parts[-1][0]}".upper()
        return name_parts[0][:2].upper()
    return user.username[:2].upper()