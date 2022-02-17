from django import template

register = template.Library()


@register.inclusion_tag("admin/lab/run/run_list.html")
def show_run_list(change_list):
    return {"runs": change_list.result_list}
