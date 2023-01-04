# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt. Ltd.(<https://technaureus.com/>).

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round
from odoo.tools import pycompat
import operator as py_operator
from datetime import datetime, timedelta
from . import catch_weight

OPERATORS = {
    '<': py_operator.lt,
    '>': py_operator.gt,
    '<=': py_operator.le,
    '>=': py_operator.ge,
    '=': py_operator.eq,
    '!=': py_operator.ne
}


class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_cw_uom = fields.Many2one('uom.uom', string='CW-UOM', related='product_tmpl_id.cw_uom_id')
    cw_sales_count = fields.Float(compute='_compute_cw_sales_count', string='CW Sold')
    cw_purchased_product_qty = fields.Float(compute='_compute_purchased_product_cw_qty', string='CW Purchased')
    cw_qty_available = fields.Float(
        'CW Quantity On Hand', compute='_compute_cw_quantities', search='_search_cw_qty_available',
        digits=dp.get_precision('Product CW Unit of Measure'))

    cw_virtual_available = fields.Float(
        'CW Forecast Quantity', compute='_compute_cw_quantities', search='_search_cw_virtual_available',
        digits=dp.get_precision('Product CW Unit of Measure'))
    cw_incoming_qty = fields.Float(
        'CW Incoming', compute='_compute_cw_quantities', search='_search_incoming_cw_qty',
        digits=dp.get_precision('Product CW Unit of Measure'))
    cw_outgoing_qty = fields.Float(
        'CW Outgoing', compute='_compute_cw_quantities', search='_search_outgoing_cw_qty',
        digits=dp.get_precision('Product CW Unit of Measure'))

    @api.depends('stock_move_ids.cw_product_qty', 'stock_move_ids.state')
    def _compute_cw_quantities(self):
        res = self._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'),
                                            self._context.get('package_id'), self._context.get('from_date'),
                                            self._context.get('to_date'))
        for product in self:
            product.cw_qty_available = res[product.id]['cw_qty_available']
            product.cw_incoming_qty = res[product.id]['cw_incoming_qty']
            product.cw_outgoing_qty = res[product.id]['cw_outgoing_qty']
            product.cw_virtual_available = res[product.id]['cw_virtual_available']

    def _compute_quantities_dict(self, lot_id, owner_id, package_id, from_date=False, to_date=False):
        res = super(ProductProduct, self)._compute_quantities_dict(lot_id, owner_id, package_id, from_date=from_date,
                                                                   to_date=to_date)
        cw_domain_quant_loc, cw_domain_move_in_loc, cw_domain_move_out_loc = self._get_domain_locations()
        cw_domain_quant = [('product_id', 'in', self.ids)] + cw_domain_quant_loc
        dates_in_the_past = False
        to_date = fields.Datetime.to_datetime(to_date)
        if to_date and to_date < fields.Datetime.now():
            dates_in_the_past = True
        cw_domain_move_in = [('product_id', 'in', self.ids)] + cw_domain_move_in_loc
        cw_domain_move_out = [('product_id', 'in', self.ids)] + cw_domain_move_out_loc
        if lot_id is not None:
            cw_domain_quant += [('lot_id', '=', lot_id)]
        if owner_id is not None:
            cw_domain_quant += [('owner_id', '=', owner_id)]
            cw_domain_move_in += [('restrict_partner_id', '=', owner_id)]
            cw_domain_move_out += [('restrict_partner_id', '=', owner_id)]
        if package_id is not None:
            cw_domain_quant += [('package_id', '=', package_id)]
        if dates_in_the_past:
            cw_domain_move_in_done = list(cw_domain_move_in)
            cw_domain_move_out_done = list(cw_domain_move_out)
        if from_date:
            cw_domain_move_in += [('date', '>=', from_date)]
            cw_domain_move_out += [('date', '>=', from_date)]
        if to_date:
            cw_domain_move_in += [('date', '<=', to_date)]
            cw_domain_move_out += [('date', '<=', to_date)]
        Move = self.env['stock.move']
        Quant = self.env['stock.quant']
        cw_domain_move_in_todo = [('state', 'not in', ('done', 'cancel', 'draft'))] + cw_domain_move_in
        cw_domain_move_out_todo = [('state', 'not in', ('done', 'cancel', 'draft'))] + cw_domain_move_out
        cw_moves_in_res = dict((item['product_id'][0], item['cw_product_qty']) for item in
                               Move.read_group(cw_domain_move_in_todo, ['product_id', 'cw_product_qty'], ['product_id'],
                                               orderby='id'))
        cw_moves_out_res = dict((item['product_id'][0], item['cw_product_qty']) for item in
                                Move.read_group(cw_domain_move_out_todo, ['product_id', 'cw_product_qty'],
                                                ['product_id'], orderby='id'))
        cw_quants_res = dict((item['product_id'][0], item['cw_stock_quantity']) for item in
                             Quant.read_group(cw_domain_quant, ['product_id', 'cw_stock_quantity'], ['product_id'],
                                              orderby='id'))
        if dates_in_the_past:
            cw_domain_move_in_done = [('state', '=', 'done'), ('date', '>', to_date)] + cw_domain_move_in_done
            cw_domain_move_out_done = [('state', '=', 'done'), ('date', '>', to_date)] + cw_domain_move_out_done
            cw_moves_in_res_past = dict((item['product_id'][0], item['cw_product_qty']) for item in
                                        Move.read_group(cw_domain_move_in_done, ['product_id', 'cw_product_qty'],
                                                        ['product_id'], orderby='id'))
            cw_moves_out_res_past = dict((item['product_id'][0], item['cw_product_qty']) for item in
                                         Move.read_group(cw_domain_move_out_done, ['product_id', 'cw_product_qty'],
                                                         ['product_id'], orderby='id'))
        for product in self.with_context(prefetch_fields=False):
            product_id = product.id
            rounding_cw = product.cw_uom_id.rounding

            if dates_in_the_past:
                cw_qty_available = cw_quants_res.get(product_id, 0.0) - cw_moves_in_res_past.get(product_id,
                                                                                                 0.0) + cw_moves_out_res_past.get(
                    product_id, 0.0)
            else:
                cw_qty_available = cw_quants_res.get(product_id, 0.0)
            res[product_id]['cw_qty_available'] = float_round(cw_qty_available, precision_rounding=rounding_cw)
            res[product_id]['cw_incoming_qty'] = float_round(cw_moves_in_res.get(product_id, 0.0), precision_rounding=rounding_cw)
            res[product_id]['cw_outgoing_qty'] = float_round(cw_moves_out_res.get(product_id, 0.0), precision_rounding=rounding_cw)
            res[product_id]['cw_virtual_available'] = float_round(cw_qty_available + res[product_id]['cw_incoming_qty'] - \
                                                      res[product_id]['cw_outgoing_qty'], precision_rounding=rounding_cw)
        return res

    def _search_cw_qty_available(self, operator, value):
        if value == 0.0 and operator == '>' and not ({'from_date', 'to_date'} & set(self.env.context.keys())):
            product_ids = self._search_cw_qty_available_new(
                operator, value, self.env.context.get('lot_id'), self.env.context.get('owner_id'),
                self.env.context.get('package_id')
            )
            return [('id', 'in', product_ids)]
        return self._search_product_cw_quantity(operator, value, 'cw_qty_available')

    def _search_cw_qty_available_new(self, operator, value, lot_id=False, owner_id=False, package_id=False):
        product_ids = set()
        domain_quant = self._get_domain_locations()[0]
        if lot_id:
            domain_quant.append(('lot_id', '=', lot_id))
        if owner_id:
            domain_quant.append(('owner_id', '=', owner_id))
        if package_id:
            domain_quant.append(('package_id', '=', package_id))
        quants_groupby = self.env['stock.quant'].read_group(domain_quant, ['product_id', 'cw_stock_quantity'],
                                                            ['product_id'], orderby='id')
        for quant in quants_groupby:
            if OPERATORS[operator](quant['cw_stock_quantity'], value):
                product_ids.add(quant['product_id'][0])
        return list(product_ids)

    def _search_cw_virtual_available(self, operator, value):
        return self._search_product_cw_quantity(operator, value, 'cw_virtual_available')

    def _search_product_cw_quantity(self, operator, value, field):
        if field not in ('cw_qty_available', 'cw_virtual_available', 'cw_incoming_qty', 'cw_outgoing_qty'):
            raise UserError(_('Invalid domain left operand %s') % field)
        if operator not in ('<', '>', '=', '!=', '<=', '>='):
            raise UserError(_('Invalid domain operator %s') % operator)
        if not isinstance(value, (float, int)):
            raise UserError(_('Invalid domain right operand %s') % value)

        ids = []
        for product in self.with_context(prefetch_fields=False).search([]):
            if OPERATORS[operator](product[field], value):
                ids.append(product.id)
        return [('id', 'in', ids)]

    def _search_incoming_cw_qty(self, operator, value):
        return self._search_product_cw_quantity(operator, value, 'cw_incoming_qty')

    def _search_outgoing_cw_qty(self, operator, value):
        return self._search_product_cw_quantity(operator, value, 'cw_outgoing_qty')

    @api.model
    def get_theoretical_cw_quantity(self, product_id, location_id, lot_id=None, package_id=None, owner_id=None,
                                    to_uom=None):
        product_id = self.env['product.product'].browse(product_id)
        product_id.check_access_rights('read')
        product_id.check_access_rule('read')

        location_id = self.env['stock.location'].browse(location_id)
        lot_id = self.env['stock.production.lot'].browse(lot_id)
        package_id = self.env['stock.quant.package'].browse(package_id)
        owner_id = self.env['res.partner'].browse(owner_id)
        to_uom = self.env['uom.uom'].browse(to_uom)
        quants = self.env['stock.quant']._gather(product_id, location_id, lot_id=lot_id, package_id=package_id,
                                                 owner_id=owner_id, strict=True)
        theoretical_cw_quantity = sum([quant.cw_stock_quantity for quant in quants])

        if theoretical_cw_quantity and to_uom and product_id.cw_uom_id != to_uom:
            theoretical_cw_quantity = product_id.cw_uom_id._compute_quantity(theoretical_cw_quantity, to_uom)
        return theoretical_cw_quantity

    def _is_price_based_on_cw(self, type):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return False
        if self._is_cw_product():
            if type == 'sale':
                if self.sale_price_base and self.sale_price_base == 'cwuom':
                    return True
                elif self.sale_price_base and self.sale_price_base == 'uom':
                    return False
                elif self.categ_id.sale_price_base == 'cwuom':
                    return True
            elif type == 'purchase':
                if self.purchase_price_base and self.purchase_price_base == 'cwuom':
                    return True
                elif self.purchase_price_base and self.purchase_price_base == 'uom':
                    return False
                elif self.categ_id.purchase_price_base == 'cwuom':
                    return True
            else:
                return False
        else:
            return False

    def _is_cw_product(self):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return False
        else:
            if self.product_tmpl_id.catch_weight_ok:
                return True
            else:
                return False

    @api.multi
    def _compute_cw_sales_count(self):
        r = {}
        if not self.user_has_groups('sales_team.group_sale_salesman'):
            return r
        date_from = fields.Datetime.to_string(fields.datetime.now() - timedelta(days=365))
        domain = [
            ('state', 'in', ['sale', 'done']),
            ('product_id', 'in', self.ids),
            ('date', '>', date_from)
        ]
        for group in self.env['sale.report'].read_group(domain, ['product_id', 'product_cw_uom_qty'], ['product_id']):
            r[group['product_id'][0]] = group['product_cw_uom_qty']
        for product in self:
            product.cw_sales_count = float_round(r.get(product.id, 0), precision_rounding=product.product_cw_uom.rounding)
        return r

    @api.multi
    def _compute_purchased_product_cw_qty(self):
        date_from = fields.Datetime.to_string(fields.datetime.now() - timedelta(days=365))
        domain = [
            ('state', 'in', ['purchase', 'done']),
            ('product_id', 'in', self.mapped('id')),
            ('date_order', '>', date_from)
        ]
        PurchaseOrderLines = self.env['purchase.order.line'].search(domain)
        order_lines = self.env['purchase.order.line'].read_group(domain, ['product_id', 'product_cw_uom_qty'],
                                                                 ['product_id'])
        purchased_data = dict([(data['product_id'][0], data['product_cw_uom_qty']) for data in order_lines])
        for product in self:
            product.cw_purchased_product_qty = float_round(purchased_data.get(product.id, 0),
                                                           precision_rounding=product.product_cw_uom.rounding)

    def _compute_product_price(self):
        to_uom = self.env.context.get('cw_uom', False)
        if to_uom:
            to_uom = self.env['uom.uom'].browse(to_uom)
            if self.cw_uom_id != to_uom:
                catch_weight.add_to_context(self, {'cw_product_uom': self.cw_uom_id,
                                                   'cw_to_uom': to_uom})
        return super(ProductProduct, self)._compute_product_price()

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ProductProduct, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                          submenu=submenu)
        if self._context.get('location') and isinstance(self._context['location'], pycompat.integer_types):
            location = self.env['stock.location'].browse(self._context['location'])
            fields = res.get('fields')
            if fields:
                if location.usage == 'supplier':
                    if fields.get('cw_virtual_available'):
                        res['fields']['cw_virtual_available']['string'] = _('Future CW Receipts')
                    if fields.get('cw_qty_available'):
                        res['fields']['cw_qty_available']['string'] = _('Received CW Qty')
                elif location.usage == 'internal':
                    if fields.get('cw_virtual_available'):
                        res['fields']['cw_virtual_available']['string'] = _('Forecasted CW Quantity')
                elif location.usage == 'customer':
                    if fields.get('cw_virtual_available'):
                        res['fields']['cw_virtual_available']['string'] = _('Future CW Deliveries')
                    if fields.get('cw_qty_available'):
                        res['fields']['cw_qty_available']['string'] = _('Delivered CW Qty')
                elif location.usage == 'inventory':
                    if fields.get('cw_virtual_available'):
                        res['fields']['cw_virtual_available']['string'] = _('Future CW P&L')
                    if fields.get('cw_qty_available'):
                        res['fields']['cw_qty_available']['string'] = _('P&L CW Qty')
                elif location.usage == 'procurement':
                    if fields.get('cw_virtual_available'):
                        res['fields']['cw_virtual_available']['string'] = _('Future CW Qty')
                    if fields.get('cw_qty_available'):
                        res['fields']['cw_qty_available']['string'] = _('Unplanned CW Qty')
                elif location.usage == 'production':
                    if fields.get('cw_virtual_available'):
                        res['fields']['cw_virtual_available']['string'] = _('Future CW Productions')
                    if fields.get('cw_qty_available'):
                        res['fields']['cw_qty_available']['string'] = _('Produced CW Qty')
        return res


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _default_cw_uom(self):
        return self.env.ref('uom.product_uom_gram').id

    def get_cw_qty(self):
        return 0

    cw_sales_count = fields.Float(compute='_compute_cw_sales_count', string='CW Sold')
    cw_purchased_product_qty = fields.Float(compute='_compute_purchased_product_cw_qty', string='CW Purchased')
    cw_uom_id = fields.Many2one('uom.uom', string="Catch Weight UOM", default=_default_cw_uom)
    cw_uom_name = fields.Char(string='CW-UOM Name', related='cw_uom_id.name', readonly=True)
    catch_weight_ok = fields.Boolean('Catch Weight Product', default=False)
    sale_price_base = fields.Selection([('uom', 'UOM'), ('cwuom', 'CW-UOM')], string="Sale Price Base")
    purchase_price_base = fields.Selection([('uom', 'UOM'), ('cwuom', 'CW-UOM')], string="Purchase Price Base")
    cw_virtual_available = fields.Float(
        'CW Forecasted Quantity', compute='_compute_cw_quantities', search='_search_virtual_available',
        digits=dp.get_precision('Product CW Unit of Measure'))
    cw_qty_available = fields.Float(
        'CW Quantity On Hand', compute='_compute_cw_quantities', search='_search_cw_qty_available',
        digits=dp.get_precision('Product CW Unit of Measure'))
    cw_incoming_qty = fields.Float(
        'CW Incoming', compute='_compute_cw_quantities', search='_search_incoming_cw_qty',
        digits=dp.get_precision('Product CW Unit of Measure'))
    cw_outgoing_qty = fields.Float(
        'CW Outgoing', compute='_compute_cw_quantities', search='_search_outgoing_cw_qty',
        digits=dp.get_precision('Product CW Unit of Measure'))

    def _compute_cw_quantities(self):
        res = self._compute_quantities_dict()
        for template in self:
            if template.product_variant_id._is_cw_product():
                template.cw_qty_available = res[template.id]['cw_qty_available']
                template.cw_virtual_available = res[template.id]['cw_virtual_available']
                template.cw_incoming_qty = res[template.id]['cw_incoming_qty']
                template.cw_outgoing_qty = res[template.id]['cw_outgoing_qty']

    def _compute_quantities_dict(self):
        res = super(ProductTemplate, self)._compute_quantities_dict()
        variants_available = self.mapped('product_variant_ids')._product_available()
        for template in self:
            cw_qty_available = 0
            cw_virtual_available = 0
            cw_incoming_qty = 0
            cw_outgoing_qty = 0
            for p in template.product_variant_ids:
                cw_qty_available += variants_available[p.id]["cw_qty_available"]
                cw_virtual_available += variants_available[p.id]["cw_virtual_available"]
                cw_incoming_qty += variants_available[p.id]["cw_incoming_qty"]
                cw_outgoing_qty += variants_available[p.id]["cw_outgoing_qty"]
                res[template.id].update({
                    "cw_qty_available": cw_qty_available,
                    "cw_virtual_available": cw_virtual_available,
                    "cw_incoming_qty": cw_incoming_qty,
                    "cw_outgoing_qty": cw_outgoing_qty
                })
        return res

    def _search_cw_qty_available(self, operator, value):
        domain = [('cw_qty_available', operator, value)]
        product_variant_ids = self.env['product.product'].search(domain)
        return [('product_variant_ids', 'in', product_variant_ids.ids)]

    def _search_cw_virtual_available(self, operator, value):
        domain = [('cw_virtual_available', operator, value)]
        product_variant_ids = self.env['product.product'].search(domain)
        return [('product_variant_ids', 'in', product_variant_ids.ids)]

    def _search_incoming_cw_qty(self, operator, value):
        domain = [('cw_incoming_qty', operator, value)]
        product_variant_ids = self.env['product.product'].search(domain)
        return [('product_variant_ids', 'in', product_variant_ids.ids)]

    def _search_outgoing_cw_qty(self, operator, value):
        domain = [('cw_outgoing_qty', operator, value)]
        product_variant_ids = self.env['product.product'].search(domain)
        return [('product_variant_ids', 'in', product_variant_ids.ids)]

    @api.multi
    def write(self, vals):
        if 'cw_uom_id' in vals:
            new_cw_uom = self.env['uom.uom'].browse(vals['cw_uom_id'])
            updated = self.filtered(lambda template: template.cw_uom_id != new_cw_uom)
            done_moves = self.env['stock.move'].search(
                [('product_id', 'in', updated.with_context(active_test=False).mapped('product_variant_ids').ids)],
                limit=1)
            if done_moves:
                raise UserError(_(
                    "You cannot change the CW unit of measure as there are already stock moves for this product."
                    " If you want to change the CW unit of measure, you should rather archive this product "
                    "and create a new one."))
        res = super(ProductTemplate, self).write(vals)
        if self.catch_weight_ok and self.type == 'service':
            raise UserError(_('A CatchWeight product cannot be a service product.'))
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('catch_weight_ok') and vals.get('type') == 'service':
                raise UserError(_('A CatchWeight product cannot be a service product.'))
        return super(ProductTemplate, self).create(vals_list)

    @api.multi
    @api.depends('product_variant_ids.cw_sales_count')
    def _compute_cw_sales_count(self):
        for template in self:
            if template.catch_weight_ok:
                template.cw_sales_count = float_round(
                sum([p.cw_sales_count for p in template.with_context(active_test=False).product_variant_ids]),
                precision_rounding=template.cw_uom_id.rounding)
            else:
                template.cw_sales_count = 0.0

    @api.multi
    def _compute_purchased_product_cw_qty(self):
        for template in self:
            if template.catch_weight_ok:
                template.cw_purchased_product_qty = float_round(
                    sum([p.cw_purchased_product_qty for p in template.product_variant_ids]),
                    precision_rounding=template.cw_uom_id.rounding)
            else:
                template.cw_purchased_product_qty = 0.0


class ProductPackaging(models.Model):
    _inherit = "product.packaging"

    def _default_cw_uom(self):
        return self.env.ref('uom.product_uom_gram').id

    cw_uom_id = fields.Many2one('uom.uom', string="Catch Weight UOM", default=_default_cw_uom)
    cw_qty = fields.Float('Contained CW Qty', help="The cw qty products you can have per pallet or box.")
    catch_weight_ok = fields.Boolean(invisible='1', related='product_id.catch_weight_ok')
