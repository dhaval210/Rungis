# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).


from odoo import api, models, _


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.onchange('quantity_done', 'cw_qty_done', 'product_uom', 'product_cw_uom')
    def _onchange_qty(self):
        for move in self:
            if self.env.user.has_group('tis_cw_average_qty.group_deviation_warning') and \
                    move.product_id._is_cw_product() and move.quantity_done > 0 and move.cw_qty_done > 0:
                warning_mess = move.product_id.check_deviation_warning(move.cw_qty_done, move.quantity_done,
                                                                       move.product_uom, move.product_cw_uom)
                return {'warning': warning_mess}
