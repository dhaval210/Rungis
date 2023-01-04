from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class Product(models.Model):
    _inherit = 'product.product'

    qty_available_mh = fields.Float(
        'Quantity On Hand (MH)',
        compute='_compute_quantities_mh',
        digits=dp.get_precision('Product Unit of Measure')
    )

    @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state')
    def _compute_quantities_mh(self):
        Quant = self.env['stock.quant']
        locations_ids = self.env['stock.location'].sudo().search([
            ('id', 'child_of', 1069)  # meckenheim stock
        ])
        domain_quant = [
            ('product_id', 'in', self.ids),
            ('location_id', 'in', locations_ids.ids),
        ]
        quants_res = dict((item['product_id'][0], item['quantity']) for item in Quant.sudo().read_group(domain_quant, ['product_id', 'quantity'], ['product_id'], orderby='id'))
        for product in self:
            product_id = product.id
            product.qty_available_mh = quants_res.get(product_id, 0.0)

    # Be aware that the exact same function exists in product.template
    def action_open_quant_mh(self):
        self.env['stock.quant']._merge_quants()
        self.env['stock.quant']._unlink_zero_quants()
        locations_ids = self.env['stock.location'].search([
            ('id', 'child_of', 1069)  # meckenheim stock
        ])        
        action = self.env.ref('stock.product_open_quants').read()[0]
        action['domain'] = [
            ('product_id', '=', self.id),
            ('location_id', 'in', locations_ids.ids),
        ]
        # action['context'] = {'search_default_internal_loc': 1}
        return action


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    qty_available_mh = fields.Float(
        'Quantity On Hand', compute='_compute_quantities_mh',
        digits=dp.get_precision('Product Unit of Measure')
    )

    def _compute_quantities_mh(self):
        for template in self:
            qty_available_mh = 0
            for p in template.product_variant_ids:
                qty_available_mh += p.qty_available_mh
            template.qty_available_mh = qty_available_mh


    # Be aware that the exact same function exists in product.product
    def action_open_quant_mh(self):
        self.env['stock.quant']._merge_quants()
        self.env['stock.quant']._unlink_zero_quants()
        products = self.mapped('product_variant_ids')
        action = self.env.ref('stock.product_open_quants').read()[0]
        locations_ids = self.env['stock.location'].search([
            ('id', 'child_of', 1069)  # meckenheim stock
        ])        
        action['domain'] = [
            ('product_id', 'in', products.ids),
            ('location_id', 'in', locations_ids.ids),
        ]
        action['context'] = {'search_default_internal_loc': 1}
        return action
