# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo.addons import decimal_precision as dp
from odoo import api, fields, models, _
from odoo.tools import float_utils
from odoo.exceptions import UserError


class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    product_cw_uom_id = fields.Many2one('uom.uom', string='CW-UOM', related='product_id.cw_uom_id', required=True)
    product_cw_uom_category_id = fields.Many2one(string='CW Uom category', related='product_cw_uom_id.category_id',
                                                 readonly=True)
    cw_product_qty = fields.Float('Real CW Quantity',
                                  digits=dp.get_precision('Product CW Unit of Measure'), default=0)
    theoretical_cw_qty = fields.Float(
        'Theoretical CW Quantity', compute='_compute_theoretical_cw_qty',
        digits=dp.get_precision('Product CW Unit of Measure'), readonly=True, store=True)
    catch_weight_ok = fields.Boolean(invisible='1', related='product_id.catch_weight_ok')

    @api.one
    @api.depends('location_id', 'product_id', 'package_id', 'product_cw_uom_id', 'company_id', 'prod_lot_id',
                 'partner_id')
    def _compute_theoretical_cw_qty(self):
        if not self.product_id:
            self.theoretical_cw_qty = 0
            return
        theoretical_cw_qty = self.product_id.get_theoretical_cw_quantity(
            self.product_id.id,
            self.location_id.id,
            lot_id=self.prod_lot_id.id,
            package_id=self.package_id.id,
            owner_id=self.partner_id.id,
            to_uom=self.product_cw_uom_id.id,
        )
        self.theoretical_cw_qty = theoretical_cw_qty

    def _get_move_values(self, qty, location_id, location_dest_id, out):
        res = super(InventoryLine, self)._get_move_values(qty, location_id, location_dest_id, out)
        for line in self:
            if float_utils.float_compare(line.theoretical_cw_qty, line.cw_product_qty,
                                         precision_rounding=line.product_id.cw_uom_id.rounding) == 0:
                continue
            cw_qty = abs(line.theoretical_cw_qty - line.cw_product_qty)
            res.update({
                'product_cw_uom': self.product_cw_uom_id.id,
                'product_cw_uom_qty': cw_qty, })
            x = res.get('move_line_ids')
            order = x[0][2]
            order.update({
                'product_cw_uom_qty': 0,
                'product_cw_uom': self.product_cw_uom_id.id,
                'cw_qty_done': cw_qty,
            })
        return res

    @api.model
    def create(self, values):
        if 'product_id' in values and 'product_cw_uom_id' not in values:
            values['product_cw_uom_id'] = self.env['product.product'].browse(values['product_id']).cw_uom_id.id
        return super(InventoryLine, self).create(values)

    @api.onchange('product_id')
    def _onchange_product(self):
        res = super(InventoryLine, self)._onchange_product()
        domain = res.get('domain')
        if self.product_id:
            self.product_cw_uom_id = self.product_id.cw_uom_id
            domain.update({
                'product_cw_uom_id': [('category_id', '=', self.product_id.cw_uom_id.category_id.id)]
            })
        return res

    @api.onchange('product_id', 'location_id', 'product_cw_uom_id', 'prod_lot_id', 'partner_id', 'package_id')
    def onchange_cw_quantity_context(self):
        if self.product_id and self.location_id and self.product_id.cw_uom_id.category_id == self.product_cw_uom_id.category_id:
            self._compute_theoretical_cw_qty()
            self.cw_product_qty = self.theoretical_cw_qty


class Inventory(models.Model):
    _inherit = "stock.inventory"

    total_cw_qty = fields.Float('Total CW Quantity', compute='_compute_total_cw_qty')

    @api.one
    @api.depends('product_id', 'line_ids.cw_product_qty')
    def _compute_total_cw_qty(self):
        if self.product_id:
            self.total_cw_qty = sum(self.mapped('line_ids').mapped('cw_product_qty'))
        else:
            self.total_cw_qty = 0

    def action_reset_product_qty(self):
        super(Inventory, self).action_reset_product_qty()
        self.mapped('line_ids').write({'cw_product_qty': 0})
        return True

    def _get_inventory_lines_values(self):
        vals = super(Inventory, self)._get_inventory_lines_values()
        locations = self.env['stock.location'].search([('id', 'child_of', [self.location_id.id])])
        domain = ' location_id in %s'
        args = (tuple(locations.ids),)
        Product = self.env['product.product']
        quant_products = self.env['product.product']
        products_to_filter = self.env['product.product']

        if self.company_id:
            domain += ' AND company_id = %s'
            args += (self.company_id.id,)
        if self.partner_id:
            domain += ' AND owner_id = %s'
            args += (self.partner_id.id,)
        if self.lot_id:
            domain += ' AND lot_id = %s'
            args += (self.lot_id.id,)
        if self.product_id:
            domain += ' AND product_id = %s'
            args += (self.product_id.id,)
            products_to_filter |= self.product_id
        if self.package_id:
            domain += ' AND package_id = %s'
            args += (self.package_id.id,)
        if self.category_id:
            categ_products = Product.search([('categ_id', '=', self.category_id.id)])
            domain += ' AND product_id = ANY (%s)'
            args += (categ_products.ids,)
            products_to_filter |= categ_products
        self.env.cr.execute("""SELECT product_id, sum(quantity) as product_qty,  sum(cw_stock_quantity) as cw_product_qty, location_id, lot_id as prod_lot_id, package_id, owner_id as partner_id
                    FROM stock_quant
                    WHERE %s
                    GROUP BY product_id, location_id, lot_id, package_id, partner_id """ % domain, args)
        for product_data in self.env.cr.dictfetchall():
            for order in vals:
                if order.get('product_id') == product_data.get('product_id'):
                    order.update({
                        'product_cw_uom': Product.browse(product_data['product_id']).cw_uom_id.id,
                        'theoretical_cw_qty': product_data['cw_product_qty'],
                        'cw_product_qty': product_data['cw_product_qty'],
                    })
        return vals

    def _action_done(self):
        res = super(Inventory, self)._action_done()
        for order in self:
            for line in order.line_ids:
                if line.product_id._is_cw_product():
                    if line.product_qty == 0 and line.cw_product_qty > 0:
                        raise UserError(_('Please enter the Quantity for %s.') % (line.product_id.name))
                    if line.product_qty > 0 and line.cw_product_qty == 0:
                        raise UserError(_('Please enter the CW Quantity for %s.') % (line.product_id.name))
                    if line.cw_product_qty < 0:
                        raise UserError(_('Catch Weight quantity cannot be negative for %s.') % (line.product_id.name))
        return res
