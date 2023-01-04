# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, fields, models, _


class ChangeProductionQty(models.TransientModel):
    _inherit = 'change.production.qty'

    @api.model
    def _update_product_to_produce(self, production, qty, old_qty):
        res = super(ChangeProductionQty, self)._update_product_to_produce(production, qty, old_qty)
        done_moves = production.move_finished_ids.filtered(
            lambda x: x.state == 'done' and x.product_id == production.product_id)
        if production.product_id._is_cw_product():
            cw_qty_produced = production.product_id.cw_uom_id._compute_quantity(sum(done_moves.mapped('cw_product_qty')),
                                                                      production.product_cw_uom_id)
            cw_qty = production.cw_product_qty - cw_qty_produced
            production_move = production.move_finished_ids.filtered(
                lambda x: x.product_id.id == production.product_id.id and x.state not in ('done', 'cancel'))
            if production_move:
                production_move.write({'product_cw_uom_qty': cw_qty})
        return res

    @api.multi
    def change_prod_qty(self):
        for wizard in self:
            production = wizard.mo_id
            factor = production.product_uom_id._compute_quantity(wizard.product_qty,
                                                                 production.bom_id.product_uom_id) / production.bom_id.product_qty
            qty = production.bom_id.cw_product_qty * factor
            production.write({'cw_product_qty': qty})
        return super(ChangeProductionQty, self).change_prod_qty()
