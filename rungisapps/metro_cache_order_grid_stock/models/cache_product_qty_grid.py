from odoo import api, fields, models


class CacheOrderGrid(models.Model):
    _name = 'cache.product.qty.grid'
    _description = 'Product Qty Grid'

    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        required=True
    )
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        required=True
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        related='product_tmpl_id.product_variant_id',
        store=True
    )
    qty_on_hand = fields.Float(compute="_compute_qty_on_hand")

    @api.depends('warehouse_id.lot_stock_id', 'product_id')
    def _compute_qty_on_hand(self):
        for rec in self:
            quants = self.env['stock.quant'].search([
                ('location_id', 'child_of', rec.warehouse_id.lot_stock_id.id),
                ('product_id', '=', rec.product_id.id),
            ])
            if len(quants) > 0:
                rec.qty_on_hand = sum(quants.mapped('quantity'))
            else:
                rec.qty_on_hand = 0
        return True
