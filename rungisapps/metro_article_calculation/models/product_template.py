# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import odoo.addons.decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    preview = fields.Html(string="Preview", readonly=True)
    landed_cost = fields.Float("Landed Cost")

    def generate_preview(self):
        landed_cost = self.env['average.landed.cost.lines'].search(
            [('product_id', '=', self.product_variant_id.id)
             ], order='create_date desc', limit=1)
        if landed_cost:
            picking_ids = landed_cost.line_id.picking_ids
            for seller in self.seller_ids:
                pickers = picking_ids.filtered(lambda p: p.partner_id.id == seller.name.id)
                if pickers:
                    seller.avg_land_cost = landed_cost.average_landed_cost
        html = self.env.ref(
            'metro_article_calculation.product_temp_report_pricecalculation').render(
            self.id)[0]
        self.preview = html


class ProductProduct(models.Model):
    _inherit = 'product.product'

    preview = fields.Html(string="Preview")
    landed_cost = fields.Float("Landed Cost")

    def generate_preview(self):
        landed_cost = self.env['average.landed.cost.lines'].search(
            [('product_id', '=', self.id)
             ], order='create_date desc', limit=1)
        if landed_cost:

            picking_ids = landed_cost.line_id.picking_ids
            for seller in self.seller_ids:
                pickers = picking_ids.filtered(lambda p: p.partner_id.id == seller.name.id)
                if pickers:
                    seller.avg_land_cost = landed_cost.average_landed_cost
        html = self.env.ref(
            'metro_article_calculation.product_product_report_pricecalculation').render(
            self.id)[0]
        self.preview = html


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    discount_calculation = fields.Float(
        string='Total_discount  (%)',
        digits=dp.get_precision('Discount'),
        compute="compute_total"
    )
    avg_land_cost = fields.Float(
        string='Average Landed Cost',
    )
    catch_weight_ok = fields.Boolean(string="Catch Weight Product", related="product_tmpl_id.catch_weight_ok")

    @api.depends('discount', 'discount2', 'discount3')
    def compute_total(self):
        for res in self:
            values = res.price
            if res.discount:
                value = (res.discount / 100) * res.price
                values = res.price - value
            if res.discount2:
                value1 = (res.discount2 / 100) * values
                values = values - value1
            if res.discount3:
                values2 = (res.discount3 / 100) * values
                values = values - values2
            res.discount_calculation = values


