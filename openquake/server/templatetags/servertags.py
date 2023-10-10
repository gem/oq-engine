from django import template

register = template.Library()


@register.filter
def imt(string):
    return string.split('-')[1]
