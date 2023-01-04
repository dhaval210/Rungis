

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools import float_compare
from odoo.exceptions import Warning

class StockMove(models.Model):
    _inherit = 'stock.move'


    def _update_reserved_quantity(self, need, available_quantity, location_id, lot_id=None, package_id=None, owner_id=None, strict=True):
        self.ensure_one()
        product_ids = {}
        # recompute the remaining quantities all at once
        res = super(StockMove,self)._update_reserved_quantity(need, available_quantity, location_id, lot_id, package_id, owner_id, strict)
        for line in self.mapped('move_line_ids'):
            if line.package_id:
                if line.product_id.id not in product_ids.keys():
                    product_ids[line.product_id.id] = [1,self.env['stock.location']]
                else:
                    loc = line.picking_id.location_dest_id.with_context(skip_loc=product_ids[line.product_id.id]).get_putaway_strategy(line.product_id)   
                    if loc:
                        product_ids[line.product_id.id][1] = loc
                        line.write({'location_dest_id': loc.id})
                    product_ids[line.product_id.id][0] += 1
        return res