from django import template

register = template.Library()


@register.filter
def get_imt(string):
    """
    Get imt from a string like 'disagg_by_src-PGA.png'
    """
    return string.split('-')[1].rstrip('.png')


@register.filter
def humanize_number(value):
    """
    Converts a large number into a human-readable format, e.g., 1000 -> 1K
    """
    try:
        value = float(value)
    except (ValueError, TypeError):
        return str(value)
    if value < 1000:
        return f'{value:.2f}'
    if 1000 <= value < 1000000:
        return f'{value/1000:.2f}K'
    if 1000000 <= value < 1000000000:
        return f'{value/1000000:.2f}M'
    return f'{value/1000000000:.2f}B'


@register.simple_tag()
def no_optional_cookie_groups_except_hide_cookie_bar_exist(request):
    from cookie_consent.models import CookieGroup
    if (CookieGroup.objects.filter(is_required=False).exclude(
            varname='hide_cookie_bar_group').count() == 0 and
            CookieGroup.objects.filter(is_required=True).count() > 0):
        return True
    else:
        return False


@register.simple_tag()
def hide_cookie_bar_accepted(request):
    from cookie_consent.util import get_cookie_value_from_request
    return get_cookie_value_from_request(
        request, "hide_cookie_bar_group",
        "hide_cookie_bar_group:hide_cookie_bar")


@register.filter
def addstr(arg1, arg2):
    """
    concatenate arg1 & arg2
    NOTE: if arguments are numeric, the Django 'add' filter would sum them instead of
    concatenating them as strings, so we need this new filter to make sure that
    arguments are always treated as strings
    """
    return str(arg1) + str(arg2)
