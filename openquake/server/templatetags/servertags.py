from django import template
from openquake.baselib.general import humanize_number

register = template.Library()


@register.filter
def get_imt(string):
    """
    Get imt from a string like 'disagg_by_src-PGA.png'
    """
    return string.split('-')[1].rstrip('.png')


register.filter(humanize_number)


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
