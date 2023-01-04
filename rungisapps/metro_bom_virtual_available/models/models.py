from odoo import api, models, fields
import math


class ProductProduct(models.Model):

    _inherit = "product.product"

    bom_virtual_available = fields.Integer('# can be manufactured', compute='_compute_bom_virtual_available')

    def _compute_bom_virtual_available(self):
        for record in self:
            if len(record.bom_ids) > 0:
                available = 2**31
                for bom_line in record.bom_ids[0].bom_line_ids:
                    available = min(available, math.floor(bom_line.product_id.virtual_available / bom_line.product_qty) * record.bom_ids[0].product_qty)
                record.bom_virtual_available = available

    @api.multi
    def action_view_components(self):
        self.ensure_one()
        components = self.bom_ids[0].mapped('bom_line_ids.product_id').ids if len(self.bom_ids) > 0 else []
        action = {
            'name': 'Bom virtual available',
            'res_model': 'stock.quant',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'context': "{'group_by': ['location_id','product_id']}",
            'view_mode': 'tree,form,pivot',
            'domain': [('product_id', 'in', components), ('location_id.usage', 'in', ['view', 'internal'])],
            'context': {'group_by': ['product_id', 'location_id']},
        }
        return action


class Product(models.Model):

    _inherit = "product.template"

    bom_virtual_available = fields.Integer('# can be manufactured', compute='_compute_bom_virtual_available')

    def _compute_bom_virtual_available(self):
        for record in self:
            if len(record.bom_ids) > 0:
                available = 2**31
                for bom_line in record.bom_ids[0].bom_line_ids:
                    available = min(available, math.floor(bom_line.product_id.virtual_available / bom_line.product_qty) * record.bom_ids[0].product_qty)
                record.bom_virtual_available = available

    @api.multi
    def action_view_components(self):
        self.ensure_one()
        return self.product_variant_ids[0].action_view_components()
