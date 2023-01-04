# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt. Ltd.(<http://technaureus.com/>).

from odoo import fields, models
from odoo.tools import float_compare


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _update_received_cw_qty(self):
        super(PurchaseOrderLine, self)._update_received_cw_qty()
        for line in self.filtered(lambda x: x.move_ids and x.product_id.id not in x.move_ids.mapped('product_id').ids):
            bom = self.env['mrp.bom']._bom_find(product=line.product_id, company_id=line.company_id.id)
            if bom and bom.type == 'phantom':
                line.cw_qty_received = line._get_cw_bom_delivered(bom=bom)

    def _get_cw_bom_delivered(self, bom=False):
        self.ensure_one()

        if bom:
            moves = self.move_ids.filtered(lambda m: m.picking_id and m.picking_id.state != 'cancel')
            bom_delivered = all([move.state == 'done' for move in moves])
            if bom_delivered:
                return self.product_cw_uom_qty
            else:
                return 0.0
