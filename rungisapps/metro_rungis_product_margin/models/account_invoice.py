# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp

class InvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    purchase_price = fields.Float(string='Buy Price(unit)', compute='_compute_purchase_price', digits=dp.get_precision('EK 1'), )
    margin = fields.Float(string="Gross Profit(line)", compute='_compute_margin_invoice_line', digits=dp.get_precision('Product Price'), readonly=True, )
    margin_percent = fields.Float(compute='_compute_margin_invoice_line_perc', string="Margin(%)", readonly=True, )
    purchase_cost = fields.Float(string='Buy Price(line)', compute='_compute_purchase_cost',readonly=True,
                                  digits=dp.get_precision('Product Price'), )

    @api.depends('product_id', 'uom_id')
    def _compute_purchase_price(self):
        for il in self:
            if il.product_id:
                frm_cur = self.env.user.company_id.currency_id
                to_cur = il.currency_id
                purchase_price = il.product_id.last_purchase_price
                if il.uom_id != il.product_id.uom_id and il.uom_id:
                    purchase_price = il.product_id.uom_id._compute_price(purchase_price, il.uom_id)
                ctx = self.env.context.copy()
                ctx['date'] = il.invoice_id.date
                price = frm_cur.with_context(ctx)._convert(purchase_price, to_cur, self.env.user.company_id, il.invoice_id.date_invoice or fields.Date.today(),round=False)
                il.purchase_price = price
            else:
                il.purchase_price = 0

    @api.depends('quantity', 'price_unit', 'purchase_price', 'product_cw_uom_qty')
    def _compute_margin_invoice_line(self):
        for il in self:
            if il.price_unit and il.product_cw_uom_qty:
                il.margin = float(il.price_unit - il.purchase_price) * float(il.product_cw_uom_qty)
            elif il.price_unit and il.quantity:
                il.margin = float(il.price_unit - il.purchase_price) * float(il.quantity)
            else:
                il.margin = 0

    @api.depends('quantity', 'price_unit', 'purchase_price', 'product_cw_uom_qty')
    def _compute_margin_invoice_line_perc(self):
        for il in self:
            if il.price_unit and il.purchase_price and il.quantity:
                il.margin_percent = float(il.price_unit - il.purchase_price) / float(il.price_unit) * 100
            else:
                il.margin_percent = 0


    @api.depends('quantity', 'price_unit', 'purchase_price', 'product_cw_uom_qty')
    def _compute_purchase_cost(self):
        for il in self:
            if il.price_unit and il.purchase_price and il.product_cw_uom_qty:
                il.purchase_cost = float(il.purchase_price) * float(il.product_cw_uom_qty)
            elif il.price_unit and il.purchase_price and il.quantity:
                il.purchase_cost = float(il.purchase_price) * float(il.quantity)
            else:
                il.purchase_cost = 0


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    margin = fields.Float(compute='_compute_margin_invoice', string="Gross Profit", readonly=True, )
    margin_percent = fields.Float(compute='_compute_margin_invoice_perc', string="Margin(%)", readonly=True, )
    purchase_price = fields.Float(compute='_compute_purchase_price', string="Buy Price(unit)", readonly=True, )
    purchase_cost = fields.Float(compute='_compute_purchase_cost', string="Buy Price", readonly=True, )

    @api.onchange('amount_untaxed', 'invoice_line_ids')
    def _compute_margin_invoice(self):
        for invoice in self:
            margin = 0
            for inv_line in invoice.invoice_line_ids:
                margin += inv_line.margin
            if margin:
                invoice.margin = margin
            else:
                invoice.margin = 0

    @api.onchange('amount_untaxed', 'invoice_line_ids')
    def _compute_margin_invoice_perc(self):
        for invoice in self:
            if invoice.amount_untaxed and invoice.margin:
                invoice.margin_percent = float(invoice.margin) / float(invoice.amount_untaxed) * 100
            else:
                invoice.margin_percent = 0

    @api.onchange('amount_untaxed', 'invoice_line_ids')
    def _compute_purchase_price(self):
        for invoice in self:
            purchase_price = 0
            for inv_line in invoice.invoice_line_ids:
                purchase_price += inv_line.purchase_price
            if purchase_price:
                invoice.purchase_price = purchase_price
            else:
                invoice.purchase_price = 0

    @api.onchange('amount_untaxed', 'invoice_line_ids')
    def _compute_purchase_cost(self):
        for invoice in self:
            purchase_cost = 0
            for inv_line in invoice.invoice_line_ids:
                purchase_cost += inv_line.purchase_cost
            if purchase_cost:
                invoice.purchase_cost = purchase_cost
            else:
                invoice.purchase_cost = 0

    @api.onchange('amount_untaxed', 'invoice_line_ids')
    def onchange_margin_amounts_so(self):
        self._compute_margin_invoice()
        self._compute_margin_invoice_perc()
        self._compute_purchase_cost()


