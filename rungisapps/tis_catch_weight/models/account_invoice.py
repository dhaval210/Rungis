# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from . import catch_weight


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
                 'invoice_id.date_invoice', 'invoice_id.date', 'product_cw_uom_qty')
    def _compute_price(self):
        if not self.product_id._is_cw_product():
            return super(AccountInvoiceLine, self)._compute_price()
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        inv_type = 'purchase' if self.invoice_id.type in ['in_invoice', 'in_refund'] else 'sale'
        quantity = self.product_cw_uom_qty if self.product_id._is_price_based_on_cw(inv_type) else self.quantity
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, quantity, product=self.product_id,
                                                          partner=self.invoice_id.partner_id)
        self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else quantity * price
        self.price_total = taxes['total_included'] if taxes else self.price_subtotal
        if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            price_subtotal_signed = self.invoice_id.currency_id.with_context(
                date=self.invoice_id._get_currency_rate_date()).compute(price_subtotal_signed,
                                                                        self.invoice_id.company_id.currency_id)
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign

    product_cw_uom = fields.Many2one('uom.uom', string='CW-UOM')
    product_cw_uom_qty = fields.Float(string='CW-Qty', default=0.0,
                                      digits=dp.get_precision('Product CW Unit of Measure'))
    catch_weight_ok = fields.Boolean(invisible='1', related='product_id.catch_weight_ok')

    @api.multi
    @api.onchange('product_id')
    def _onchange_product_id(self):
        super(AccountInvoiceLine, self)._onchange_product_id()
        if self.product_id._is_cw_product():
            self.product_cw_uom = self.product_id.cw_uom_id

    @api.onchange('product_cw_uom')
    def _onchange_cw_uom(self):
        warning = {}
        result = {}
        if self.product_id.cw_uom_id.category_id.id != self.product_cw_uom.category_id.id:
            warning = {
                'title': _('Warning!'),
                'message': _(
                    'The selected unit of measure has to be in the same category as the product Catch Weight unit of measure.'),
            }
            self.product_cw_uom = self.product_id.uom_id.id
        if warning:
            result['warning'] = warning
        return result

    @api.onchange('uom_id', 'product_cw_uom')
    def _onchange_uom_id(self):
        inv_type = 'purchase' if self.invoice_id.type in ['in_invoice', 'in_refund'] else 'sale'
        if self.product_cw_uom and self.product_id._is_price_based_on_cw(inv_type):
            catch_weight.add_to_context(self, {'cw_product_uom': self.product_id.cw_uom_id,
                                               'cw_to_uom': self.product_cw_uom})
        return super(AccountInvoiceLine, self)._onchange_uom_id()


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _prepare_invoice_line_from_po_line(self, line):
        res = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(line)
        if line.product_id.purchase_method == 'purchase':
            qty = line.product_cw_uom_qty - line.cw_qty_invoiced
        else:
            qty = line.cw_qty_received - line.cw_qty_invoiced
        res.update({
            'product_cw_uom': line.product_cw_uom.id,
            'product_cw_uom_qty': qty,
        })
        return res

    @api.model
    def invoice_line_move_line_get(self):
        res = super(AccountInvoice, self).invoice_line_move_line_get()
        for line in self.invoice_line_ids:
            if line.quantity == 0:
                continue
            res[0].update({
                'cw_quantity': line.product_cw_uom_qty,
            })
        return res

    @api.model
    def tax_line_move_line_get(self):
        res = super(AccountInvoice, self).tax_line_move_line_get()
        if len(res) >= 1:
            res[0].update({
                'cw_quantity': 1,
            })
        return res

    @api.multi
    def get_taxes_values(self):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(AccountInvoice, self).get_taxes_values()
        tax_grouped = {}
        round_curr = self.currency_id.round
        for line in self.invoice_line_ids:
            inv_type = 'purchase' if line.invoice_id.type in ['in_invoice', 'in_refund'] else 'sale'
            quantity = line.product_cw_uom_qty if line.product_id._is_price_based_on_cw(inv_type) else line.quantity
            if not line.account_id:
                continue
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.invoice_line_tax_ids.compute_all(price_unit, self.currency_id, quantity, line.product_id,
                                                          self.partner_id)['taxes']
            for tax in taxes:
                val = self._prepare_tax_line_vals(line, tax)
                key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)

                if key not in tax_grouped:
                    tax_grouped[key] = val
                    tax_grouped[key]['base'] = round_curr(val['base'])
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += round_curr(val['base'])
        return tax_grouped
