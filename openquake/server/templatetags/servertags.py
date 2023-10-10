from django import template

register = template.Library()


@register.filter
def get_disagg_by_src_imt(string):
    """
    Get imt from a string like 'disagg_by_src-PGA'
    """
    return string.split('-')[1]
