from odoo import models, fields, api


class SalesOrderLine(models.Model):
    _inherit = 'sale.order.line'

    lot_name = fields.Many2one('stock.production.lot', string='Lot')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        for rec in self.sale_id.order_line:
            for lt in self.mapped('move_line_ids_without_package'):
                if not rec.lot_name:
                    rec.lot_name = lt.sudo().filtered(
                        lambda x: x.product_id.id == rec.product_id.id).lot_id.id
        return res

