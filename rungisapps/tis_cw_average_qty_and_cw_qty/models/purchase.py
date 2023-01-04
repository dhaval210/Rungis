# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import fields, api, models, _
from odoo.tools import float_round
from odoo.exceptions import UserError


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    order_by = fields.Selection([('p-uom', 'P-UoM'), ('cw-uom', 'CW-UoM')], string='Order By', default='p-uom')

    @api.multi
    @api.onchange('product_id')
    def onchange_product_id(self):
        self.order_by = 'p-uom'
        return super(PurchaseOrderLine, self).onchange_product_id()

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        if self.order_by == 'p-uom':
            super(PurchaseOrderLine, self)._onchange_quantity()
            context = self._context.copy()
            if context.get('cw_params'):
                context['cw_params'].update({'flag': 1})
            else:
                context['cw_params'] = {'flag': 1}
            self.env.context = context
        elif self._context.get('cw_params') and self._context.get('cw_params').get('flag') == 0:
            return
        else:
            raise UserError(_('You can change CW quantity only if order by CW-UoM '))

    @api.onchange('product_cw_uom', 'product_cw_uom_qty')
    def _onchange_cw_quantity(self):
        if self.product_id._is_cw_product() and self.product_id.average_cw_quantity and self.order_by == 'cw-uom':
            if self.product_cw_uom == self.product_id.cw_uom_id:
                quantity = self.product_cw_uom_qty / self.product_id.average_cw_quantity
            else:
                product_cw_uom_qty = self.product_cw_uom._compute_quantity(self.product_cw_uom_qty,
                                                                           self.product_id.cw_uom_id)
                quantity = product_cw_uom_qty / self.product_id.average_cw_quantity
            if self.product_qty != quantity:
                self.product_qty = round(quantity, 0)
            context = self._context.copy()
            if context.get('cw_params'):
                context['cw_params'].update({'flag': 0})
            else:
                context['cw_params'] = {'flag': 0}
            self.env.context = context
        elif self._context.get('cw_params') and self._context['cw_params']['flag'] == 1:
            return
        else:
            raise UserError(_('You can change quantity only if order by P-UoM '))
