from odoo import models, fields


class StockMove(models.Model):
    _inherit = 'stock.move'

    currency_id = fields.Many2one(related='product_id.currency_id', readonly=True)
    purchase_price = fields.Monetary(compute='_compute_purchase_price', string='Purchase Price',
                                     currency_field='currency_id')
    supplier = fields.Many2one('res.partner', string="Vendor", readonly=True, compute='_compute_purchase_price')
    done_qty = fields.Float(string="Done", compute='_get_done_qty')
    ordered_date = fields.Datetime(string="Date", compute="_compute_purchase_price")

    def _compute_purchase_price(self):
        for rec in self:
            record = self.env['purchase.order'].search([('name', '=', rec.origin)])
            for line in record:
                for data in line.order_line.filtered(lambda x: x.product_id.id == rec.product_id.id):
                    rec.purchase_price = data.price_unit
                    rec.supplier = data.partner_id
                    rec.ordered_date = data.date_order

    def _get_done_qty(self):
        for rec in self:
            record = self.env['stock.picking'].search([('name', '=', rec.reference)])
            for line in record:
                for data in line.move_line_ids_without_package.filtered(lambda x: x.product_id.id == rec.product_id.id):
                    rec.done_qty = data.qty_done
