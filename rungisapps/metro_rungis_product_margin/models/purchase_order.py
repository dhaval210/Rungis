# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    sales_price = fields.Float(string='Pot. Sales Price(unit)', compute='_compute_sales_price', digits=dp.get_precision('Product Price'))
    margin = fields.Float(string="Pot. Gross Profit (line)", compute='_compute_margin_po_line', digits=dp.get_precision('Product Price'), readonly=True,)
    margin_percent = fields.Float(compute='_compute_margin_po_line_perc', string="Pot. Margin %", readonly=True, )
    sales_cost = fields.Float(string='Pot. Sales (line)', compute='_compute_sales_cost', readonly=True,
                                   digits=dp.get_precision('Product Price'))

    @api.depends('product_qty', 'price_unit', 'product_cw_uom_qty')
    def _compute_sales_price(self):
        for ol in self:
            if ol.product_id:
                frm_cur = self.env.user.company_id.currency_id
                to_cur = ol.currency_id
                sales_price = ol.product_id.lst_price
                if ol.product_uom != ol.product_id.uom_po_id and ol.product_uom:
                    sales_price = ol.product_id.uom_po_id._compute_price(sales_price, ol.product_uom)
                ctx = self.env.context.copy()
                ctx['date'] = ol.order_id.date_order
                price = frm_cur.with_context(ctx)._convert(sales_price, to_cur, self.env.user.company_id, ol.order_id.date_order or fields.Date.today(),round=False)
                ol.sales_price = price
            else:
                ol.sales_price = 0

    @api.depends('product_qty', 'price_unit', 'sales_price', 'product_cw_uom_qty')
    def _compute_margin_po_line(self):
        for ol in self:
            if ol.price_unit and ol.product_cw_uom_qty:
                ol.margin = float(ol.sales_price - ol.price_unit) * float(ol.product_cw_uom_qty)
            elif ol.price_unit and ol.product_qty:
                ol.margin = float(ol.sales_price - ol.price_unit) * float(ol.product_qty)
            else:
                ol.margin = 0

    @api.depends('product_qty', 'price_unit', 'sales_price', 'product_cw_uom_qty')
    def _compute_margin_po_line_perc(self):
        for ol in self:
            if ol.price_unit and ol.sales_price and ol.product_qty:
                ol.margin_percent = float(ol.sales_price - ol.price_unit) / float(ol.price_unit)
            else:
                ol.margin_percent = 0


    @api.depends('product_qty', 'price_unit', 'sales_price', 'product_cw_uom_qty')
    def _compute_sales_cost(self):
        for ol in self:
            if ol.price_unit and ol.sales_price and ol.product_cw_uom_qty:
                ol.sales_cost = float(ol.sales_price) * float(ol.product_cw_uom_qty)
            elif ol.price_unit and ol.sales_price and ol.product_qty:
                ol.sales_cost = float(ol.sales_price) * float(ol.product_qty)
            else:
                ol.sales_cost = 0

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sales_price = fields.Float(compute='_compute_sales_price', string="Pot.Sales Price(unit)", readonly=True, )
    margin = fields.Float(compute='_compute_margin_po', string="Pot. Gross Profit", readonly=True, )
    margin_percent = fields.Float(compute='_compute_margin_po_perc', string="Margin(%)", readonly=True, )
    sales_cost = fields.Float(compute='_compute_sales_cost', string="Pot.Sales", readonly=True, )

    @api.depends('amount_untaxed', 'order_line')
    def _compute_margin_po(self):
        for order in self:
            margin = 0
            for ol in order.order_line:
                margin += ol.margin
            if margin:
                order.margin = margin
            else:
                order.margin = 0

    @api.depends('amount_untaxed', 'order_line')
    def _compute_margin_po_perc(self):
        for order in self:
            if order.amount_untaxed and order.margin:
                order.margin_percent = float(order.margin) / float(order.amount_untaxed)
            else:
                order.margin_percent = 0

    @api.depends('amount_untaxed', 'order_line')
    def _compute_sales_price(self):
        for order in self:
            sales_price = 0
            for ol in order.order_line:
                sales_price += ol.sales_price
            if sales_price:
                order.sales_price = sales_price
            else:
                order.sales_price = 0

    @api.depends('amount_untaxed', 'order_line')
    def _compute_sales_cost(self):
        for order in self:
            sales_cost = 0
            for ol in order.order_line:
                sales_cost += ol.sales_cost
            if sales_cost:
                order.sales_cost = sales_cost
            else:
                order.sales_cost = 0

    @api.onchange('amount_untaxed', 'order_line')
    def onchange_margin_amounts_so(self):
        self._compute_margin_po()
        self._compute_margin_po_perc()



