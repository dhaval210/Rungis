# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _compute_cw_qty_delivered(self):
        super(SaleOrderLine, self)._compute_cw_qty_delivered()
        for line in self:
            if line.qty_delivered_method == 'stock_move':
                bom = self.env['mrp.bom']._bom_find(product=line.product_id, company_id=line.company_id.id)
                if bom and bom.type == 'phantom':
                    moves = line.move_ids.filtered(lambda m: m.picking_id and m.picking_id.state != 'cancel')
                    bom_delivered = moves and all([move.state == 'done' for move in moves])
                    if bom_delivered:
                        line.cw_qty_delivered = line.product_cw_uom_qty
                    else:
                        line.cw_qty_delivered = 0.0

    def _get_qty_procurement(self):
        self.ensure_one()
        bom = self.env['mrp.bom']._bom_find(product=self.product_id)
        if bom and bom.type == 'phantom' and 'previous_product_cw_uom_qty' in self.env.context:
            return self.env.context['previous_product_cw_uom_qty'].get(self.id, 0.0)
        return super(SaleOrderLine, self)._get_qty_procurement()
