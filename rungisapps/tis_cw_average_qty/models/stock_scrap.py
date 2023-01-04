# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, models, _


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    @api.onchange('scrap_qty', 'product_uom_id')
    def _onchange_qty(self):
        for line in self:
            if line.product_id._is_cw_product():
                if line.product_uom_id == line.product_id.uom_id:
                    line.scrap_cw_qty = line.scrap_qty * line.product_id.average_cw_quantity
                else:
                    quantity = line.product_uom_id._compute_quantity(line.scrap_qty, line.product_id.uom_id)
                    line.scrap_cw_qty = quantity * line.product_id.average_cw_quantity
            if self.env.user.has_group('tis_cw_average_qty.group_deviation_warning') and \
                    line.product_id._is_cw_product() and line.scrap_cw_qty > 0 and line.scrap_qty > 0:
                warning_mess = line.product_id.check_deviation_warning(line.scrap_cw_qty, line.scrap_qty,
                                                                       line.product_uom_id,
                                                                       line.product_cw_uom)
                return {'warning': warning_mess}

    @api.onchange('scrap_cw_qty', 'product_cw_uom')
    def _onchange_cw_qty(self):
        for line in self:
            if line.product_id._is_cw_product() and line.scrap_cw_qty > 0 and line.scrap_qty > 0:
                warning_mess = line.product_id.check_deviation_warning(line.scrap_cw_qty, line.scrap_qty,
                                                                       line.product_uom_id,
                                                                       line.product_cw_uom)
                return {'warning': warning_mess}

