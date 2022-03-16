from django import template

register = template.Library()

@register.simple_tag
def create_list(*args):
    return list(args)
