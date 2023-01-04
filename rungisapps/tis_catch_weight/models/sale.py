# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import models, fields, api, _
from functools import partial
from odoo.tools.misc import formatLang
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare
from . import catch_weight


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        for line in self.order_line:
            if line.product_id._is_cw_product():
                if line.product_cw_uom_qty == 0 and line.product_uom_qty != 0:
                    raise UserError(_("Please enter the CW Quantity for %s") % (line.product_id.name))
                elif line.product_cw_uom_qty != 0 and line.product_uom_qty == 0:
                    raise UserError(_("Please enter the Quantity for %s") % (line.product_id.name))
            else:
                line.product_cw_uom_qty = 0
                line.product_cw_uom = None
        return super(SaleOrder, self).action_confirm()

    def _amount_by_group(self):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(SaleOrder, self)._amount_by_group()
        for order in self:
            currency = order.currency_id or order.company_id.currency_id
            fmt = partial(formatLang, self.with_context(lang=order.partner_id.lang).env, currency_obj=currency)
            res = {}
            for line in order.order_line:
                price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
                if line.product_id._is_cw_product():
                    taxes = line.tax_id.compute_all(price_reduce, quantity=line.product_cw_uom_qty,
                                                    product=line.product_id, partner=order.partner_shipping_id)['taxes']
                else:
                    taxes = line.tax_id.compute_all(price_reduce, quantity=line.product_uom_qty,
                                                    product=line.product_id, partner=order.partner_shipping_id)['taxes']
                for tax in line.tax_id:
                    group = tax.tax_group_id
                    res.setdefault(group, {'amount': 0.0, 'base': 0.0})
                    for t in taxes:
                        if t['id'] == tax.id or t['id'] in tax.children_tax_ids.ids:
                            res[group]['amount'] += t['amount']
                            res[group]['base'] += t['base']
            res = sorted(res.items(), key=lambda l: l[0].sequence)
            order.amount_by_group = [(
                l[0].name, l[1]['amount'], l[1]['base'],
                fmt(l[1]['amount']), fmt(l[1]['base']),
                len(res),
            ) for l in res]


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def write(self, values):
        so_lines = self.env['sale.order.line']
        if 'product_cw_uom_qty' in values:
            precision = self.env['decimal.precision'].precision_get('Product CW Unit of Measure')
            so_lines = self.filtered(
                lambda r: r.state == 'sale' and float_compare(r.product_cw_uom_qty, values['product_cw_uom_qty'],
                                                              precision_digits=precision) == -1)
            self.filtered(
                lambda r: r.state == 'sale' and float_compare(r.product_cw_uom_qty, values['product_cw_uom_qty'],
                                                              precision_digits=precision) != 0)._update_line_cw_quantity(
                values)
        previous_product_cw_uom_qty = {line.id: line.product_cw_uom_qty for line in so_lines}
        res = super(SaleOrderLine, self).write(values)
        picking = self.order_id.picking_ids.filtered(lambda x: x.state not in ('done'))
        if so_lines and 'product_uom_qty' not in values:
            if not picking:
                raise ValidationError(_('You cannot change cw quantities!'))
            else:
                so_lines.with_context(
                    previous_product_cw_uom_qty=previous_product_cw_uom_qty)._action_launch_stock_rule()
        return res

    def _update_line_cw_quantity(self, values):
        orders = self.mapped('order_id')
        for order in orders:
            order_lines = self.filtered(lambda x: x.order_id == order)
            msg = "<b>The ordered quantity has been updated.</b><ul>"
            for line in order_lines:
                msg += "<li> %s:" % (line.product_id.display_name,)
                msg += "<br/>" + _("Ordered CW Quantity") + ": %s -> %s <br/>" % (
                    line.product_cw_uom_qty, float(values['product_cw_uom_qty']),)
                if line.product_id.type in ('consu', 'product'):
                    msg += _("Delivered CW Quantity") + ": %s <br/>" % (line.cw_qty_delivered,)
                msg += _("Invoiced CW Quantity") + ": %s <br/>" % (line.cw_qty_invoiced,)
            msg += "</ul>"
            order.message_post(body=msg)
        precision = self.env['decimal.precision'].precision_get('Product CW Unit of Measure')
        line_products = self.filtered(lambda l: l.product_id.type in ['product', 'consu'])
        if line_products.mapped('cw_qty_delivered') and float_compare(values['product_cw_uom_qty'],
                                                                      max(line_products.mapped('cw_qty_delivered')),
                                                                      precision_digits=precision) == -1:
            raise UserError(_('You cannot decrease the ordered CW quantity below the CW delivered quantity.\n'
                              'Create a return first.'))

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'product_cw_uom_qty')
    def _compute_amount(self):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(SaleOrderLine, self)._compute_amount()
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            if line.product_id._is_price_based_on_cw('sale'):
                quantity = line.product_cw_uom_qty
            else:
                quantity = line.product_uom_qty
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, quantity,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.depends('cw_qty_invoiced', 'cw_qty_delivered', 'product_cw_uom_qty', 'order_id.state')
    def _get_to_invoice_cw_qty(self):
        for line in self:
            if line.order_id.state in ['sale', 'done']:
                if line.product_id.invoice_policy == 'order':
                    line.cw_qty_to_invoice = line.product_cw_uom_qty - line.cw_qty_invoiced
                else:
                    line.cw_qty_to_invoice = line.cw_qty_delivered - line.cw_qty_invoiced
            else:
                line.cw_qty_to_invoice = 0

    @api.depends('invoice_lines.invoice_id.state', 'invoice_lines.product_cw_uom_qty')
    def _get_invoice_cw_qty(self):
        for line in self:
            cw_qty_invoiced = 0.0
            for invoice_line in line.invoice_lines:
                if invoice_line.invoice_id.state != 'cancel':
                    if invoice_line.invoice_id.type == 'out_invoice':
                        cw_qty_invoiced += invoice_line.product_cw_uom._compute_quantity(
                            invoice_line.product_cw_uom_qty, line.product_cw_uom)
                    elif invoice_line.invoice_id.type == 'out_refund':
                        cw_qty_invoiced -= invoice_line.product_cw_uom._compute_quantity(
                            invoice_line.product_cw_uom_qty, line.product_cw_uom)
            line.cw_qty_invoiced = cw_qty_invoiced

    @api.multi
    @api.depends('move_ids.state', 'move_ids.scrapped', 'move_ids.cw_qty_done', 'move_ids.product_cw_uom')
    def _compute_cw_qty_delivered(self):
        for line in self:  # TODO: maybe one day, this should be done in SQL for performance sake
            if line.product_id._is_cw_product() and line.qty_delivered_method == 'stock_move':
                qty = 0.0
                for move in line.move_ids.filtered(
                        lambda r: r.state == 'done' and not r.scrapped and line.product_id == r.product_id):
                    if move.location_dest_id.usage == "customer":
                        if not move.origin_returned_move_id or (move.origin_returned_move_id and move.to_refund):
                            qty += move.product_cw_uom._compute_quantity(move.cw_qty_done, line.product_cw_uom)
                    elif move.location_dest_id.usage != "customer" and move.to_refund:
                        qty -= move.product_cw_uom._compute_quantity(move.cw_qty_done, line.product_cw_uom)
                line.cw_qty_delivered = qty

    cw_qty_delivered = fields.Float(string='CW Delivered', compute='_compute_cw_qty_delivered', store=True, copy=False,
                                    digits=dp.get_precision('Product CW Unit of Measure'),
                                    default=0.0)
    cw_qty_to_invoice = fields.Float(
        compute='_get_to_invoice_cw_qty', string='CW To Invoice', store=True, readonly=True,
        digits=dp.get_precision('Product CW Unit of Measure'))
    cw_qty_invoiced = fields.Float(
        compute='_get_invoice_cw_qty', string='CW Invoiced', store=True, readonly=True,
        digits=dp.get_precision('Product CW Unit of Measure'))

    product_cw_uom = fields.Many2one('uom.uom', string='CW-UOM')
    catch_weight_ok = fields.Boolean(invisible='1', related='product_id.catch_weight_ok')
    product_cw_uom_qty = fields.Float(string='CW-Qty', default=0.0,
                                      digits=dp.get_precision('Product CW Unit of Measure'))
    cw_product_qty = fields.Float(compute='_compute_product_cw_qty', string='CW Quantity')

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        if self.product_id._is_cw_product():
            self.product_cw_uom = self.product_id.cw_uom_id
            domain_dict = res.get('domain')
            domain_dict.update({'product_cw_uom': [('category_id', '=', self.product_id.cw_uom_id.category_id.id)]})
        return res

    @api.multi
    def _prepare_invoice_line(self, qty):
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        res.update({
            'product_cw_uom': self.product_cw_uom.id,
            'product_cw_uom_qty': self.cw_qty_to_invoice,
        })
        return res

    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        res = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        precision = self.env['decimal.precision'].precision_get('Product CW Unit of Measure')
        get_param = self.env['ir.config_parameter'].sudo().get_param
        for line in self:
            cw_qty = line._get_cw_qty_procurement()
            procurement_uom = line.product_cw_uom
            quant_uom = line.product_id.cw_uom_id
            if float_compare(cw_qty, line.product_cw_uom_qty, precision_digits=precision) >= 0:
                continue
            product_cw_qty = line.product_cw_uom_qty - cw_qty
            if procurement_uom.id != quant_uom.id and get_param('stock.propagate_uom') != '1':
                product_cw_qty = line.product_cw_uom._compute_quantity(product_cw_qty, quant_uom,
                                                                       rounding_method='HALF-UP')
                procurement_uom = quant_uom
            res.update({
                'product_cw_uom': procurement_uom.id,
                'product_cw_uom_qty': product_cw_qty,
            })
        return res

    @api.depends('product_id', 'product_cw_uom', 'product_cw_uom_qty')
    def _compute_product_cw_qty(self):
        for line in self:
            if not line.product_id or not line.product_cw_uom or not line.product_cw_uom_qty:
                return 0.0
            line.cw_product_qty = line.product_cw_uom._compute_quantity(line.product_cw_uom_qty,
                                                                        line.product_id.cw_uom_id)

    @api.onchange('product_id')
    def _onchange_product_id_uom_check_cw_availability(self):
        if self.product_id._is_cw_product():
            if not self.product_cw_uom or (
                    self.product_id.cw_uom_id.category_id.id != self.product_cw_uom.category_id.id):
                self.product_cw_uom = self.product_id.cw_uom_id
            self._onchange_product_id_check_cw_availability()

    @api.onchange('product_cw_uom_qty', 'product_cw_uom', 'route_id')
    def _onchange_product_id_check_cw_availability(self):
        if not self.product_id or not self.product_cw_uom_qty or not self.product_cw_uom:
            self.product_packaging = False
            return {}
        if self.product_id.type == 'product':
            precision = self.env['decimal.precision'].precision_get('Product CW Unit of Measure')
            product = self.product_id.with_context(
                warehouse=self.order_id.warehouse_id.id,
                lang=self.order_id.partner_id.lang or self.env.user.lang or 'en_US'
            )
            cw_product_qty = self.product_cw_uom._compute_quantity(self.product_cw_uom_qty, self.product_id.cw_uom_id)
            if float_compare(product.cw_virtual_available, cw_product_qty, precision_digits=precision) == -1:
                is_available = self._check_routing()
                if not is_available:
                    message = _('You plan to sell %s %s but you only have %s %s available in %s warehouse.') % \
                              (self.product_cw_uom_qty, self.product_cw_uom.name, product.cw_virtual_available,
                               product.cw_uom_id.name, self.order_id.warehouse_id.name)
                    if (product.cw_virtual_available - self.product_id.cw_virtual_available) == -1:
                        message += _('\nThere are %s %s available across all warehouses.') % \
                                   (self.product_id.cw_virtual_available, product.cw_uom_id.name)

                    warning_mess = {
                        'title': _('Not enough inventory!'),
                        'message': message
                    }
                    return {'warning': warning_mess}
        return {}

    def _get_cw_qty_procurement(self):
        self.ensure_one()
        cw_qty = 0.0
        for move in self.move_ids.filtered(lambda r: r.state != 'cancel'):
            if move.picking_code == 'outgoing':
                cw_qty += move.product_cw_uom._compute_quantity(move.product_cw_uom_qty, self.product_cw_uom,
                                                                rounding_method='HALF-UP')
            elif move.picking_code == 'incoming':
                cw_qty -= move.product_cw_uom._compute_quantity(move.product_cw_uom_qty, self.product_cw_uom,
                                                                rounding_method='HALF-UP')
        return cw_qty

    @api.depends('price_total', 'product_uom_qty')
    def _get_price_reduce_tax(self):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(SaleOrderLine, self)._get_price_reduce_tax()
        for line in self:
            if line.product_id._is_cw_product():
                line.price_reduce_taxinc = line.price_total / line.product_cw_uom_qty if line.product_cw_uom_qty else 0.0
            else:
                line.price_reduce_taxinc = line.price_total / line.product_uom_qty if line.product_uom_qty else 0.0

    @api.depends('price_subtotal', 'product_uom_qty')
    def _get_price_reduce_notax(self):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(SaleOrderLine, self)._get_price_reduce_notax()
        for line in self:

            if line.product_id._is_cw_product():
                line.price_reduce_taxexcl = line.price_subtotal / line.product_cw_uom_qty if line.product_cw_uom_qty else 0.0
            else:
                line.price_reduce_taxexcl = line.price_subtotal / line.product_uom_qty if line.product_uom_qty else 0.0

    @api.onchange('product_cw_uom', 'product_cw_uom_qty')
    def cw_product_uom_change(self):
        if not self.product_id._is_price_based_on_cw('sale'):
            return
        if not self.product_uom or not self.product_id or not self.product_cw_uom:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position'),
                cw_uom=self.product_cw_uom.id
            )
            self.price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product),
                                                                                      product.taxes_id, self.tax_id,
                                                                                      self.company_id)

    @api.multi
    def _get_display_price(self, product):
        if not self.product_id._is_price_based_on_cw('sale'):
            return super(SaleOrderLine, self)._get_display_price(product)
        to_uom = self.product_cw_uom or False
        product_cw_uom_id = self.product_id.cw_uom_id
        if to_uom and product_cw_uom_id:
            catch_weight.add_to_context(self, {'cw_product_uom': product_cw_uom_id,
                                               'cw_to_uom': to_uom})
        return super(SaleOrderLine, self)._get_display_price(product)

    @api.multi
    def _check_package(self):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(SaleOrderLine, self)._check_package()
        if self.product_id._is_cw_product():
            default_uom = self.product_id.uom_id
            pack = self.product_packaging
            qty = self.product_uom_qty
            q = default_uom._compute_quantity(pack.qty, self.product_uom)
            default_cw_uom = pack.cw_uom_id
            cw_qty = self.product_cw_uom_qty
            cw_q = default_cw_uom._compute_quantity(pack.cw_qty, self.product_cw_uom)
            if pack.cw_qty == 0 and (cw_qty % cw_q) == 0:
                return super(SaleOrderLine, self)._check_package()
            if qty and q and (qty % q) and cw_qty and cw_q and (cw_qty % cw_q):
                newqty = qty - (qty % q) + q
                new_cwqty = cw_qty - (cw_qty % cw_q) + cw_q
                return {
                    'warning': {
                        'title': _('Warning'),
                        'message': _(
                            "This product is packaged by %.2f %s[%.2f %s]. You should sell %.2f %s[%.2f %s].") % (
                                       pack.qty, default_uom.name, pack.cw_qty, default_cw_uom.name, newqty,
                                       self.product_uom.name, new_cwqty, self.product_cw_uom.name),
                    },
                }
            return {}

    def _compute_untaxed_amount_to_invoice(self):
        for line in self:
            if not line.env.user.has_group('tis_catch_weight.group_catch_weight'):
                return super(SaleOrderLine, line)._compute_untaxed_amount_to_invoice()
            if not line.product_id._is_price_based_on_cw('sale'):
                return super(SaleOrderLine, line)._compute_untaxed_amount_to_invoice()
            else:
                amount_to_invoice = 0.0
                if line.state in ['sale', 'done']:
                    if line.product_id.invoice_policy == 'delivery':
                        price_subtotal = line.price_reduce * line.cw_qty_delivered
                    else:
                        price_subtotal = line.price_reduce * line.product_cw_uom_qty

                    amount_to_invoice = price_subtotal - line.untaxed_amount_invoiced
                line.untaxed_amount_to_invoice = amount_to_invoice

