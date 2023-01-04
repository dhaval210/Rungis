# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.tools import float_round
from odoo.exceptions import UserError


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    catch_weight_ok = fields.Boolean(invisible='1', related='product_tmpl_id.catch_weight_ok')
    cw_product_qty = fields.Float('CW Quantity', default=0.0, digits=dp.get_precision('Product CW Unit of Measure'))
    product_cw_uom_id = fields.Many2one('uom.uom', 'Product CW Unit of Measure',
                                        help="Unit of Measure (Unit of Measure) is the unit of measurement for the inventory control")

    @api.onchange('product_cw_uom_id')
    def onchange_product_cw_uom_id(self):
        res = {}
        if not self.product_cw_uom_id or not self.product_tmpl_id:
            return res
        if self.product_cw_uom_id.category_id.id != self.product_tmpl_id.cw_uom_id.category_id.id:
            self.product_cw_uom_id = self.product_tmpl_id.cw_uom_id.id
            res['warning'] = {'title': _('Warning'), 'message': _(
                'The Product Unit of Measure for Catch Weight, you chose has a different category than in the product form.')}
        return res

    @api.onchange('product_tmpl_id')
    def onchange_product_tmpl_id(self):
        super(MrpBom, self).onchange_product_tmpl_id()
        if self.product_tmpl_id:
            try:
                avg_cw_qty = self.product_tmpl_id.average_cw_quantity
            except:
                avg_cw_qty = 0
            if self.catch_weight_ok == True:
                self.product_cw_uom_id = self.product_tmpl_id.cw_uom_id.id
                self.cw_product_qty = self.product_qty * avg_cw_qty
            else:
                self.product_cw_uom_id = None
                self.cw_product_qty = 0

    @api.onchange('product_qty')
    def onchange_product_quantity_for_cw(self):
        if self.product_tmpl_id:
            try:
                avg_cw_qty = self.product_tmpl_id.average_cw_quantity
            except:
                avg_cw_qty = 0
            if self.catch_weight_ok == True:
                self.cw_product_qty = self.product_qty * avg_cw_qty
            else:
                self.cw_product_qty = 0

    @api.model
    def create(self, vals):
        if 'product_tmpl_id' in vals:
            product_tmpl_id = self.env['product.template'].browse(vals.get('product_tmpl_id'))
            if product_tmpl_id.product_variant_id._is_cw_product():
                if vals.get('product_qty') > 0 and vals.get('cw_product_qty') <= 0:
                    raise UserError(
                        _("Please enter a valid Catch Weight quantity for the product ( %s).") % product_tmpl_id.name)
        return super(MrpBom, self).create(vals)

    @api.multi
    def write(self, vals):
        res = super(MrpBom, self).write(vals)
        if self.product_tmpl_id.product_variant_id._is_cw_product():
            if self.product_qty > 0 and self.cw_product_qty <= 0:
                raise UserError(
                    _("Please enter a valid Catch Weight quantity for the product  %s.") % self.product_id.name)
        return res

    def explode(self, product, quantity, picking_type=False):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(MrpBom, self).explode(product, quantity, picking_type)
        res = super(MrpBom, self).explode(product, quantity, picking_type)
        for order in res:
            order[0][1].update({
                'cw_qty': quantity
            })
            break
        bom_lines = [(bom_line, product, quantity, False) for bom_line in self.bom_line_ids]
        while bom_lines:
            current_line, current_product, current_qty, parent_line = bom_lines[0]
            bom_lines = bom_lines[1:]
            if current_line._skip_bom_line(current_product):
                continue
            cw_params = self._context.get('cw_params', False)
            if cw_params and 'cw_quantity_factor' in cw_params:
                line_quantity = cw_params.get('cw_quantity_factor') * current_line.cw_product_qty
            else:
                line_quantity = current_qty * current_line.cw_product_qty
            bom = self._bom_find(product=current_line.product_id, picking_type=picking_type or self.picking_type_id,
                                 company_id=self.company_id.id)
            if bom.type == 'phantom':
                converted_line_quantity = current_line.product_cw_uom_id._compute_quantity(
                    line_quantity / bom.product_qty, bom.product_cw_uom_id)
                for order in res:
                    if order[0][0] == bom:
                        order[0][1].update({
                            'cw_qty': converted_line_quantity
                        })
                        break
            else:
                rounding = current_line.product_cw_uom_id.rounding
                line_cw_quantity = float_round(line_quantity, precision_rounding=rounding, rounding_method='UP')
                for order in res[1]:
                    if order[0] == current_line:
                        order[1].update({
                            'cw_qty': line_cw_quantity
                        })
                        break
        return res


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    catch_weight_ok = fields.Boolean(invisible='1', related='product_tmpl_id.catch_weight_ok')
    cw_product_qty = fields.Float(
        'CW Quantity', default=0.0,
        digits=dp.get_precision('Product CW Unit of Measure'), required=True)
    product_cw_uom_id = fields.Many2one(
        'uom.uom', 'CW UOM',
        help="Unit of Measure (Unit of Measure) is the unit of measurement for the inventory control")

    @api.onchange('product_cw_uom_id')
    def onchange_product_uom_id(self):
        res = {}
        if not self.product_uom_id or not self.product_id or not self.catch_weight_ok:
            return res
        if self.product_cw_uom_id.category_id != self.product_id.cw_uom_id.category_id:
            self.product_cw_uom_id = self.product_id.cw_uom_id.id
            res['warning'] = {'title': _('Warning'), 'message': _(
                'The Product Unit of Measure for Catch Weight you chose has a different category than in the product form.')}
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if 'product_id' in values:
                product_id = self.env['product.product'].browse(values.get('product_id'))
                if product_id._is_cw_product():
                    if values.get('product_qty') > 0 and values.get('cw_product_qty') <= 0:
                        raise UserError(
                            _("Please enter a valid Catch Weight quantity for the product  %s.") % product_id.name)
        return super(MrpBomLine, self).create(vals_list)

    @api.multi
    def write(self, vals):
        res = super(MrpBomLine, self).write(vals)
        if self.product_id._is_cw_product():
            if self.product_qty > 0 and self.cw_product_qty <=0:
                raise UserError(
                    _("Please enter a valid Catch Weight quantity for the product  %s.") % self.product_id.name)
        return res


    @api.onchange('product_id')
    def onchange_product_id(self):
        super(MrpBomLine, self).onchange_product_id()
        if self.product_id:
            try:
                avg_cw_qty = self.product_id.average_cw_quantity
            except:
                avg_cw_qty = 0
            if self.catch_weight_ok == True:
                self.product_cw_uom_id = self.product_id.cw_uom_id.id
                self.cw_product_qty = self.product_qty * avg_cw_qty
            else:
                self.product_cw_uom_id = None
                self.cw_product_qty = 0

    @api.onchange('product_qty')
    def onchange_product_qty_for_cw(self):
        if self.product_id:
            try:
                avg_cw_qty = self.product_id.average_cw_quantity
            except:
                avg_cw_qty = 0
            if self.catch_weight_ok == True:
                self.cw_product_qty = self.product_qty * avg_cw_qty
            else:
                self.cw_product_qty = 0
