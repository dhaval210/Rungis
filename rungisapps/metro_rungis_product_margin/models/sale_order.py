# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    margin_percent = fields.Float(compute='_compute_margin_sol', string="Margin(%)", readonly=True, track_visibility='onchange', copy=False)
    purchase_cost = fields.Float(compute='_compute_purchase_cost_sol', string="Buy Price(line)", readonly=True, track_visibility='onchange', copy=False)

    margin_delivered = fields.Float(string='Gross Profit(Delivered)',compute='_compute_margin_delivered', copy=False)
    margin_delivered_percent = fields.Float(string='Margin% Delivered ',compute='_compute_margin_delivered',readonly=True, copy=False)
    purchase_price_delivery = fields.Float(string='Buy Price Delivered', compute='_compute_margin_delivered', copy=False)
    purchase_delivery_cost = fields.Float(string='Buy Cost Delivered', compute='_compute_margin_delivered', copy=False )

    #@api.depends('product_id', 'price_unit', 'purchase_price', 'product_uom_qty', 'product_cw_uom_qty','price_subtotal')
    def _compute_margin(self, order_id, product_id, product_uom_id):
        frm_cur = self.env.user.company_id.currency_id
        to_cur = order_id.pricelist_id.currency_id
        purchase_price = product_id.last_purchase_price
        if product_uom_id != product_id.uom_id:
            purchase_price = product_id.uom_id._compute_price(purchase_price, product_uom_id)
        price = frm_cur._convert(
            purchase_price, to_cur, order_id.company_id or self.env.user.company_id,
            order_id.date_order or fields.Date.today(), round=False)
        return price

    @api.depends('product_id', 'purchase_price', 'product_uom_qty', 'product_cw_uom_qty', 'price_unit',
                 'price_subtotal')
    def _compute_purchase_cost_sol(self):
        for so_line in self:
            if not so_line.purchase_price:
                so_line.purchase_price = so_line.product_id.last_purchase_price
            if so_line.product_cw_uom_qty:
                so_line.purchase_cost = so_line.purchase_price * so_line.product_cw_uom_qty
            elif so_line.product_uom_qty:
                so_line.purchase_cost = so_line.purchase_price * so_line.product_uom_qty
            else:
                so_line.purchase_cost = 0

    @api.depends('product_id', 'price_unit', 'purchase_price', 'product_uom_qty', 'product_cw_uom_qty',
                  'price_subtotal')
    def _compute_margin_sol(self):
        for so_line in self:
            if not so_line.purchase_price:
                so_line.purchase_price = so_line.product_id.last_purchase_price
            if so_line.price_unit and so_line.product_uom_qty and so_line.price_subtotal:
                so_line.margin_percent = float(so_line.price_unit - so_line.purchase_price) / float(so_line.price_unit)
            else:
                so_line.margin_percent = 0

    @api.depends('product_id', 'price_unit', 'purchase_price', 'product_uom_qty', 'product_cw_uom_qty', 'price_subtotal')
    def onchange_margin_amounts_sol(self):
        self._compute_margin_sol()
        #self._compute_purchase_cost_sol()

    @api.depends('product_id', 'purchase_price', 'product_uom_qty', 'product_cw_uom_qty', 'price_unit', 'price_subtotal')
    def _product_margin(self):
        if not self.env.in_onchange:
            # prefetch the fields needed for the computation
            self.read(['price_subtotal', 'purchase_price', 'product_uom_qty', 'product_cw_uom_qty', 'order_id'])
        for line in self:
            currency = line.order_id.pricelist_id.currency_id
            price = line.purchase_price
            if line.product_cw_uom_qty:
                line.margin = currency.round(line.price_subtotal - (price * line.product_cw_uom_qty))
            else:
                line.margin = currency.round(line.price_subtotal - (price * line.product_uom_qty))

    @api.depends('margin', 'qty_delivered', 'product_uom_qty', 'product_cw_uom_qty', 'cw_qty_delivered','move_ids')
    def _compute_margin_delivered(self):
        digits = self.env['decimal.precision'].precision_get('Product Price')
        for line in self:
            if not line.qty_delivered and not line.product_uom_qty:
                continue

            purchase_price_delivery = 0.0

            currency = line.order_id.pricelist_id.currency_id

            if line.qty_delivered:
                moves = line.move_ids.filtered ( lambda x: ( x.state == 'done' and x.picking_code == 'outgoing'))
                for move in moves:
                    for move_line in move.move_line_ids:
                        lot_id = move_line.lot_id
                        if lot_id.purchase_order_ids:
                            for po_line in lot_id.purchase_order_ids[0].order_line:
                                if po_line.product_id == lot_id.product_id:
                                    purchase_price_delivery = po_line.price_unit
                if purchase_price_delivery and line.price_unit:
                    if line.cw_qty_delivered:
                        line.purchase_price_delivery = purchase_price_delivery
                        line.purchase_delivery_cost = purchase_price_delivery * line.cw_qty_delivered
                        line.margin_delivered = currency.round(line.price_subtotal - (purchase_price_delivery * line.cw_qty_delivered))
                        line.margin_delivered_percent = float(line.price_unit - purchase_price_delivery) / float(line.price_unit)
                    else:
                        line.purchase_price_delivery = purchase_price_delivery
                        line.purchase_delivery_cost = purchase_price_delivery * line.qty_delivered
                        line.margin_delivered = currency.round(
                            line.price_subtotal - (purchase_price_delivery * line.qty_delivered))
                        line.margin_delivered_percent = float(line.price_unit - purchase_price_delivery) / float(
                            line.price_unit)
                else:
                    line.margin_delivered_percent = 0



    @api.model
    def create(self, vals):
        vals.update(self._prepare_add_missing_fields(vals))

        # Calculation of the margin for programmatic creation of a SO line. It is therefore not
        # necessary to call product_id_change_margin manually
        if 'purchase_price' not in vals and 'purchase_cost' not in vals and ('display_type' not in vals or not vals['display_type']):
            order_id = self.env['sale.order'].browse(vals['order_id'])
            product_id = self.env['product.product'].browse(vals['product_id'])
            product_uom_id = self.env['uom.uom'].browse(vals['product_uom'])

            vals['purchase_price'] = self._compute_margin(order_id, product_id, product_uom_id)
            vals['purchase_cost'] = self._compute_purchase_cost_sol()

        return super(SaleOrderLine, self).create(vals)



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    margin_percent = fields.Float(compute='_compute_margin_so', string="Margin(%)", readonly=True, track_visibility='onchange', copy=False)
    purchase_cost = fields.Float(compute='_compute_purchase_cost_so', string="Buy Price", readonly=True, track_visibility='onchange', copy=False)

    margin_delivered = fields.Float(string='Gross Profit(Delivered)', compute='_compute_margin_delivery_so', copy=False )
    margin_delivered_percent = fields.Float(string='Margin% Delivered ', compute='_compute_margin_delivery_so',
                                            readonly=True, copy=False )
    purchase_delivery_cost = fields.Float(string='Buy Cost Delivered', compute='_compute_margin_delivery_so', )

    delivery_status = fields.Selection(selection=[('nothing', 'To Deliver'), ('delivered', 'Delivered'),
        ('processing', 'Processing')], string='Delivery Status',readonly=True, copy=False, default='nothing')


    @api.depends('order_line.purchase_cost')
    def _compute_purchase_cost_so(self):
        if not self.env.in_onchange:
            # prefetch the fields needed for the computation
            self.read(['order_line', 'amount_untaxed', 'purchase_cost'])
        for order in self:
            purchase_cost = 0
            for order_line in order.order_line:
                purchase_cost += order_line.purchase_cost
            if purchase_cost:
                order.purchase_cost = purchase_cost
            else:
                order.purchase_cost = 0

    @api.depends('order_line.purchase_cost', 'global_discount_ids', 'amount_untaxed')
    def _product_margin(self):
        if not self.env.in_onchange:
            # prefetch the fields needed for the computation
            self.read(['order_line', 'amount_untaxed', 'purchase_cost'])
        for order in self:
            order._check_global_discounts_sanity()
            if order.amount_untaxed:
                order.margin = float(order.amount_untaxed) - float(order.purchase_cost)
            else:
                order.margin = 0

    @api.depends('margin', 'amount_untaxed')
    def _compute_margin_so(self):
        if not self.env.in_onchange:
            # prefetch the fields needed for the computation
            self.read(['order_line', 'amount_untaxed', 'margin'])
        for order in self:
            if order.amount_untaxed and order.margin :
                order.margin_percent = float(order.margin) / float(order.amount_untaxed)
            else:
                order.margin_percent = 0

    @api.depends('order_line.qty_delivered', 'order_line.purchase_delivery_cost', 'amount_untaxed', 'global_discount_ids')
    def _compute_margin_delivery_so(self):
        if not self.env.in_onchange:
            # prefetch the fields needed for the computation
            self.read(['order_line', 'amount_untaxed', 'purchase_cost'])
        for order in self:
            order._check_global_discounts_sanity()
            purchase_delivery_cost = 0
            for order_line in order.order_line:
                purchase_delivery_cost += order_line.purchase_delivery_cost
            if purchase_delivery_cost:
                order.purchase_delivery_cost = purchase_delivery_cost
                order.margin_delivered = float(order.amount_untaxed) - float(purchase_delivery_cost)
                order.margin_delivered_percent = (float(order.amount_untaxed) - float(purchase_delivery_cost)) / float(order.amount_untaxed)
            else:
                order.purchase_delivery_cost = 0
                order.margin_delivered = 0
                order.margin_delivered_percent = 0

    @api.depends('amount_untaxed', 'order_line')
    def onchange_margin_amounts_so(self):
        self._compute_margin_so()
        #self._compute_purchase_cost_so()



class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        if self.picking_type_code == 'outgoing' and self.sale_id:
            self.sale_id.delivery_status = 'delivered'
        return res


