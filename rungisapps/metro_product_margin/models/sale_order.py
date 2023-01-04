# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    margin_percent = fields.Float(compute='_compute_margin_so', string="Margin inc. LC(%)", readonly=True)
    landed_costs = fields.Float(compute='_compute_landed_cost_so', string="Landed Costs", readonly=True)

    def _compute_landed_cost_so(self):
        for order in self:
            landed_costs = 0
            for so_line in order.order_line:
                landed_costs += so_line.landed_costs * so_line.product_uom_qty
            if landed_costs:
                order.landed_costs = landed_costs
            else:
                order.landed_costs = 0

    def _compute_margin_so(self):
        for order in self:
            if order.amount_untaxed and order.margin and not order.amount_untaxed == order.margin:
                order.margin_percent = float(order.margin - order.landed_costs) / float(order.amount_untaxed) * 100
            else:
                order.margin_percent = 0

    @api.onchange('amount_untaxed', 'order_line')
    def onchange_margin_amounts_so(self):
        self._compute_landed_cost_so()
        self._compute_margin_so()

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    margin_percent = fields.Float(compute='_compute_margin_sol', string="Margin inc. LC(%)", readonly=True)
    landed_costs = fields.Float(compute='_compute_landed_cost_sol', string="Landed Costs", readonly=True)

    def _compute_landed_cost_sol(self):
        for so_line in self:
            if so_line.product_id.landed_cost_ids:
                landed_costs = 0
                for lc in so_line.product_id.landed_cost_ids:
                    landed_costs += so_line.purchase_price * lc.percent/100
                so_line.landed_costs = landed_costs
            else:
                so_line.landed_costs = 0

    def _compute_margin_sol(self):
        for so_line in self:
            if so_line.price_unit and so_line.purchase_price and so_line.product_uom_qty and so_line.price_subtotal:
                so_line.margin_percent = float(so_line.price_unit - so_line.purchase_price - so_line.landed_costs) / float(so_line.price_unit) * 100
            else:
                so_line.margin_percent = 0

    @api.onchange('product_id', 'price_unit', 'purchase_price', 'product_uom_qty', 'price_subtotal')
    def onchange_margin_amounts_sol(self):
        self._compute_landed_cost_sol()
        self._compute_margin_sol()
