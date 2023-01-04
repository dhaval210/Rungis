# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import fields, api, models, _
from odoo.addons import decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = "product.template"

    average_cw_quantity = fields.Float(string='Average CW Quantity', digits=dp.get_precision('Product CW Unit of Measure'),
                                       compute='_compute_avg_qty', inverse='_set_avg_qty', store=True)
    max_deviation = fields.Float(string='Maximum Deviation')

    @api.depends('product_variant_ids')
    def _compute_avg_qty(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.average_cw_quantity = template.product_variant_ids.average_cw_quantity
        for template in (self - unique_variants):
            template.average_cw_quantity = 0.0

    def _set_avg_qty(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.average_cw_quantity = template.average_cw_quantity

    @api.model_create_multi
    def create(self, vals_list):
        templates = super(ProductTemplate, self).create(vals_list)
        if "create_product_product" not in self._context:
            templates.with_context(create_from_tmpl=True).create_variant_ids()
        for template, vals in zip(templates, vals_list):
            related_vals = {}

            if vals.get('average_cw_quantity'):
                related_vals['average_cw_quantity'] = vals['average_cw_quantity']
            if related_vals:
                template.write(related_vals)

        return templates

class ProductProduct(models.Model):
    _inherit = 'product.product'

    average_cw_quantity = fields.Float(string='Average CW Quantity',
                                       digits=dp.get_precision('Product CW Unit of Measure'))

    def check_deviation_warning(self, cw_qty, qty, uom, cw_uom):
        cw_uom_qty = cw_uom._compute_quantity(cw_qty, self.cw_uom_id)
        uom_qty = uom._compute_quantity(qty, self.uom_id)
        if self.average_cw_quantity:
            deviation = self.average_cw_quantity * (self.max_deviation / 100)
            deviation_max_value = self.average_cw_quantity + deviation
            deviation_min_value = abs(self.average_cw_quantity - deviation)
            if (cw_uom_qty / uom_qty) < deviation_max_value:
                deviation_value = abs((cw_uom_qty / uom_qty) - deviation_max_value)
            else:
                deviation_value = abs((cw_uom_qty / uom_qty) - deviation_min_value)
            if (cw_uom_qty / uom_qty) < deviation_min_value or (cw_uom_qty / uom_qty) > deviation_max_value:
                warning_mess = {
                    'title': _('Exceeds Maximum Deviation!'),
                    'message': _('\nAverage CW quantity Deviated From Expected Deviation.')
                }
                return warning_mess
        return {}
