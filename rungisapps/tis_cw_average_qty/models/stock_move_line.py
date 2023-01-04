# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import models, api, _


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.onchange('cw_qty_done', 'qty_done', 'product_uom_id', 'product_cw_uom')
    def _onchange_qty(self):
        for line in self:
            if self.env.user.has_group('tis_cw_average_qty.group_deviation_warning') and \
                    line.product_id._is_cw_product() and line.qty_done > 0 and line.cw_qty_done > 0:
                warning_mess = line.product_id.check_deviation_warning(line.cw_qty_done, line.qty_done,
                                                                       line.product_uom_id, line.product_cw_uom)
                return {'warning': warning_mess}
