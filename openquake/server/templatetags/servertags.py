from django import template

register = template.Library()


@register.filter
def get_imt(string):
    """
    Get imt from a string like 'disagg_by_src-PGA.png'
    """
    return string.split('-')[1].rstrip('.png')


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
