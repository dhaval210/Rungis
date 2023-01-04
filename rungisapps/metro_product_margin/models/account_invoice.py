# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    margin = fields.Float(compute='_compute_margin_invoice', string="Margin (Gross)", readonly=True)
    margin_lc = fields.Float(compute='_compute_margin_lc_invoice', string="Margin including LC", readonly=True)
    margin_percent = fields.Float(compute='_compute_margin_invoice_perc', string="Margin inc. LC(%)", readonly=True)
    landed_costs = fields.Float(compute='_compute_landed_cost_invoice', string="Landed Costs", readonly=True)

    def _compute_landed_cost_invoice(self):
        for invoice in self:
            landed_costs = 0
            for inv_line in invoice.invoice_line_ids:
                landed_costs += inv_line.landed_costs * inv_line.quantity
            if landed_costs:
                invoice.landed_costs = landed_costs
            else:
                invoice.landed_costs = 0

    def _compute_margin_invoice(self):
        for invoice in self:
            margin = 0
            for inv_line in invoice.invoice_line_ids:
                margin += inv_line.margin
            if margin:
                invoice.margin = margin
            else:
                invoice.margin = 0

    def _compute_margin_lc_invoice(self):
        for invoice in self:
            margin_lc = 0
            for inv_line in invoice.invoice_line_ids:
                margin_lc += inv_line.margin - inv_line.landed_costs * inv_line.quantity
            if margin_lc:
                invoice.margin_lc = margin_lc
            else:
                invoice.margin_lc = 0

    def _compute_margin_invoice_perc(self):
        for invoice in self:
            if invoice.amount_untaxed and invoice.margin_lc:
                invoice.margin_percent = float(invoice.margin_lc) / float(invoice.amount_untaxed) * 100
            else:
                invoice.margin_percent = 0

    @api.onchange('amount_untaxed', 'invoice_line_ids')
    def onchange_margin_amounts_so(self):
        self._compute_landed_cost_invoice()
        self._compute_margin_invoice()
        self._compute_margin_lc_invoice()
        self._compute_margin_invoice_perc()


class InvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    purchase_price = fields.Float(string='Cost', compute='_compute_purchase_price', digits=dp.get_precision('Product Price'), store=True)
    landed_costs = fields.Float(compute='_compute_landed_cost_invoice_line', string="Landed Costs", readonly=True, store=True)
    margin = fields.Float(string="Margin (Gross)", compute='_compute_margin_invoice_line', digits=dp.get_precision('Product Price'), readonly=True, store=True)
    margin_lc = fields.Float(string="Margin including LC", compute='_compute_margin_lc_invoice_line', digits=dp.get_precision('Product Price'), readonly=True, store=True)
    margin_percent = fields.Float(compute='_compute_margin_invoice_line_perc', string="Margin inc. LC(%)", readonly=True, store=True)

    @api.depends('product_id', 'uom_id')
    def _compute_purchase_price(self):
        for il in self:
            if il.product_id:
                frm_cur = self.env.user.company_id.currency_id
                to_cur = il.currency_id
                purchase_price = il.product_id.standard_price
                if il.uom_id != il.product_id.uom_id and il.uom_id:
                    purchase_price = il.product_id.uom_id._compute_price(purchase_price, il.uom_id)
                ctx = self.env.context.copy()
                ctx['date'] = il.invoice_id.date
                price = frm_cur.with_context(ctx).compute(purchase_price, to_cur, round=False)
                il.purchase_price = price
            else:
                il.purchase_price = 0

    @api.depends('product_id', 'product_id.landed_cost_ids', 'purchase_price', 'product_id.landed_cost_ids.percent')
    def _compute_landed_cost_invoice_line(self):
        for il in self:
            if il.product_id.landed_cost_ids:
                landed_costs = 0
                for lc in il.product_id.landed_cost_ids:
                    landed_costs += il.purchase_price * lc.percent/100
                il.landed_costs = landed_costs
            else:
                il.landed_costs = 0

    @api.depends('quantity', 'price_unit', 'purchase_price')
    def _compute_margin_invoice_line(self):
        for il in self:
            if il.price_unit and il.quantity:
                il.margin = float(il.price_unit - il.purchase_price) * float(il.quantity)
            else:
                il.margin = 0

    @api.depends('quantity', 'price_unit', 'landed_costs', 'purchase_price')
    def _compute_margin_lc_invoice_line(self):
        for il in self:
            if il.price_unit and il.purchase_price and il.quantity:
                il.margin_lc = float(il.price_unit - il.purchase_price - il.landed_costs) * float(il.quantity)
            else:
                il.margin_lc = 0

    @api.depends('quantity', 'price_unit', 'landed_costs', 'purchase_price')
    def _compute_margin_invoice_line_perc(self):
        for il in self:
            if il.price_unit and il.purchase_price and il.quantity:
                il.margin_percent = float(il.price_unit - il.purchase_price - il.landed_costs) / float(il.price_unit) * 100
            else:
                il.margin_percent = 0

    # @api.onchange('product_id', 'price_unit', 'purchase_price', 'quantity', 'price_subtotal')
    # def onchange_margin_amounts_invoice_line(self):
    #     self._compute_landed_cost_invoice_line()
    #     self._compute_margin_invoice_line()
    #     self._compute_margin_lc_invoice_line()
    #     self._compute_margin_invoice_line_perc()
