from django import template

register = template.Library()


@register.filter
def get_imt(string):
    """
    Get imt from a string like 'disagg_by_src-PGA.png'
    """
    return string.split('-')[1].rstrip('.png')


@register.simple_tag()
def no_optional_cookie_groups_exist(request):
    from cookie_consent.models import CookieGroup
    if (CookieGroup.objects.filter(is_required=False).count() == 0 and
            CookieGroup.objects.filter(is_required=True).count() > 0):
        return True
    else:
        return False
