# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).


def add_to_context(self, value):
    context = self._context.copy()
    if context.get('cw_params'):
        context['cw_params'].update(value)
    else:
        context['cw_params'] = value
    self.env.context = context
