# -*- coding: utf-8 -*-
from django.contrib.admin.widgets import AdminTextareaWidget


class ShortTextAreaWidget(AdminTextareaWidget):

    def __init__(self, attrs=None):
        final_attrs = {'rows': '3'}
        if attrs is not None:
            final_attrs.update(attrs)
        super(ShortTextAreaWidget, self).__init__(attrs=final_attrs)
