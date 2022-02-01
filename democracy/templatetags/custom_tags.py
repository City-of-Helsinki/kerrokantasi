from django.contrib.admin.templatetags.admin_modify import submit_row
from django import template

register = template.Library()


@register.inclusion_tag('admin/undelete_submit_line.html', takes_context=True)
def undelete_submit_row(context):
    """`submit_row` with a different html template"""
    return submit_row(context)
