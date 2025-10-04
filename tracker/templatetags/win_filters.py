from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter
def format_wins(content):
    """
    Convert text to bullet point format for daily wins display.
    Each new line becomes a bullet point, preserving the natural way people write lists.
    """
    if not content:
        return ""
    
    # Split by lines and filter out empty ones
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    
    if not lines:
        return ""
    
    # If there's only one line, just return it as is
    if len(lines) == 1:
        return lines[0]
    
    # Convert each line to a bullet point
    bullet_points = []
    for line in lines:
        # Remove existing bullet characters if any (•, -, *, etc.)
        clean_line = re.sub(r'^[•\-\*\+]\s*', '', line).strip()
        if clean_line:
            bullet_points.append(f'• {clean_line}')
    
    return mark_safe('<br>'.join(bullet_points))

@register.filter  
def format_wins_truncate(content, length=80):
    """
    Format wins as bullet points but truncate for preview display
    """
    if not content:
        return ""
    
    # First apply bullet formatting
    formatted = format_wins(content)
    
    # Remove HTML tags for length calculation
    text_only = re.sub(r'<[^>]+>', ' ', formatted)
    
    if len(text_only) <= length:
        return formatted
    
    # Truncate and add ellipsis
    truncated = text_only[:length-3] + '...'
    return truncated