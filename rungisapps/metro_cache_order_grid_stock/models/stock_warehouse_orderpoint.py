from odoo import models, fields


class OrderPoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    def write(self, values):
        res = super().write(values)
        for rec in self:
            data = {}
            if 'product_min_qty' in values:
                data.update({'min_qty': values['product_min_qty']})
            if 'product_max_qty' in values:
                data.update({'max_qty': values['product_max_qty']})
            if len(data) > 0:
                grid_data = self.env['cache.order.grid'].search([
                    ('product_tmpl_id', '=', rec.product_id.product_tmpl_id.id),
                    ('date', '>=', fields.Date.today()),
                ])
                grid_data.write(data)
        return res
