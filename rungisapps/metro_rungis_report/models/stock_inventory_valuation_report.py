# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StockInventoryValuationReport(models.TransientModel):
    _inherit = 'report.stock.inventory.valuation.report'

    warehouse_ids = fields.Many2many(comodel_name='stock.warehouse')

    @api.multi
    def _compute_results(self):
        self.ensure_one()
        if not self.compute_at_date:
            self.date = fields.Datetime.now()
        products = self.env['product.product']. \
            search([('type', '=', 'product'), ('qty_available', '!=', 0)]). \
            with_context(dict(to_date=self.date, company_owned=True,
                              create=False, edit=False))
        ReportLine = self.env['stock.inventory.valuation.view']
        for product in products:
            standard_price = product.standard_price
            if self.date:
                standard_price = product.get_history_price(
                    self.env.user.company_id.id,
                    date=self.date)
            purchase_price_base = "UOM"
            if product.purchase_price_base and product.purchase_price_base == 'cwuom':
                purchase_price_base = "CW-UOM"
            line = {
                'name': product.name,
                'reference': product.default_code,
                'barcode': product.barcode,
                'qty_at_date': product.qty_at_date,
                'uom_id': product.uom_id,
                'currency_id': product.currency_id,
                'cost_currency_id': product.cost_currency_id,
                'standard_price': standard_price,
                'stock_value': product.qty_at_date * standard_price if purchase_price_base == "UOM"
                else product.cw_qty_available * product.standard_price,
                'cost_method': product.cost_method,
                'cw_qty_available': product.cw_qty_available,
                'purchase_price_base': purchase_price_base,
            }
            if product.qty_at_date != 0:
                self.results += ReportLine.new(line)


class StockInventoryValuationView(models.TransientModel):
    _inherit = 'stock.inventory.valuation.view'

    cw_qty_available = fields.Float()
    purchase_price_base = fields.Char()
