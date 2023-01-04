# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, fields, models, _


class StockQuantityHistory(models.TransientModel):
    _inherit = 'stock.quantity.history'
    _description = 'Stock Quantity History'

    report_type = fields.Selection([
        ('normal', 'Normal'),
        ('xls_report', 'Excel')
    ], string=" Report Type", default="normal")
    warehouse_ids = fields.Many2many('stock.warehouse', 'wh_wiz_rel', 'wh', 'wiz', string='Warehouse')
    category_ids = fields.Many2many('product.category', 'categ_wiz_rel', 'categ', 'wiz', string='Category')

    @api.multi
    def export_cw_xls(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'stock.quantity.history'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return self.env.ref('tis_cw_stock_report_xls.cw_stock_xlsx').report_action(self, data=datas)
