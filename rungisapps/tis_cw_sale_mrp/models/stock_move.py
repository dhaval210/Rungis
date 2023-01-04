# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt. Ltd.(<http://technaureus.com/>).

from odoo import models, _


class StockMove(models.Model):
    _inherit = 'stock.move'

    def action_explode(self):
        bom = self.env['mrp.bom'].sudo()._bom_find(product=self.product_id, company_id=self.company_id.id)
        if not bom or bom.type != 'phantom':
            return self
        factor = self.product_uom._compute_quantity(self.product_uom_qty,
                                                    bom.product_uom_id) / bom.product_qty
        boms, lines = bom.sudo().explode(self.product_id, factor, picking_type=bom.picking_type_id)
        for bom_line, line_data in lines:
            context = self._context.copy()
            if not context.get('cw_params'):
                context['cw_params'] = {}
            if context['cw_params'].get('phantom'):
                context['cw_params'].get('phantom').update({bom_line: line_data['cw_qty']})
            else:
                context['cw_params']['phantom'] = {bom_line: line_data['cw_qty']}
            self.env.context = context
        return super(StockMove, self).action_explode()

    def _prepare_phantom_move_values(self, bom_line, quantity):
        res = super(StockMove, self)._prepare_phantom_move_values(bom_line, quantity)
        cw_params = self._context.get('cw_params', False)
        if cw_params and cw_params.get('phantom', False):
            res.update({
                'product_cw_uom': bom_line.product_cw_uom_id.id,
                'product_cw_uom_qty': cw_params['phantom'].get(bom_line),
            })
        return res
