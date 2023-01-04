import datetime

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, tools


class PurchaseSupply(models.Model):
    _name = 'purchase.supply'
    _auto = False
    _description = 'Purchase Supply'
    _rec_name = 'partner_id'

    supplier_number = fields.Char("Supplier Number", readonly=True)
    partner_id = fields.Many2one('res.partner', "Supplier", readonly=True)
    category_id = fields.Many2one('product.category', "Category", readonly=True)
    order_id = fields.Many2one('purchase.order', "Purchase Order", readonly=True)
    date_order = fields.Datetime("Date Order", readonly=True)
    order_weight = fields.Float("Order Weight", readonly=True)
    order_amount = fields.Float("Order Amount", readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    currency_id = fields.Many2one(related="company_id.currency_id", string="Currency", readonly=True)
    purchase_percentage_in_last_6 = fields.Float("in % Purchase volume Supplier last 6 Months",
                                                 compute="get_percentage")
    product_id = fields.Many2one('product.product', "Article", readonly=True)
    product_number = fields.Char('Art.Nr', readonly=True)
    receipt_date = fields.Datetime("Receipt Date", readonly=True)
    receipt_weight = fields.Float("Receipt Weight", readonly=True)
    receipt_amount = fields.Float("Receipt Amount", readonly=True)

    @api.depends('order_amount')
    def get_percentage(self):
        today = datetime.date.today()
        last_6 = today - relativedelta(months=6)
        purchase_ids = self.env['purchase.order'].search([('date_order', '>=', last_6)])
        list_amounts = purchase_ids.mapped('amount_untaxed')
        total_amount = sum(list_amounts)
        for recd in self:
            amount_percentage = round(100.0 * (recd.order_amount / total_amount), 2)
            recd.purchase_percentage_in_last_6 = amount_percentage

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """ CREATE or REPLACE VIEW purchase_supply AS (select row_number() OVER () as id, rp.ref as
                    supplier_number, pl.partner_id as partner_id,
                    pt.categ_id as category_id, pl.order_id as order_id,po.state as state, po.date_order
                    as date_order, ((pl.product_qty * (1/um.factor)) * pt.net_weight) as order_weight,
                    pl.price_subtotal as order_amount, po.company_id as company_id,
					pp.id as product_id, pp.default_code as product_number,
					sm.date_expected as receipt_date, sm.weight as receipt_weight,
					(sm.product_qty * sm.price_unit) as receipt_amount
                    from purchase_order_line as pl
                    left join purchase_order po on po.id = pl.order_id
                    left join res_partner rp on pl.partner_id = rp.id
                    left join product_product pp on pl.product_id = pp.id
                    left join product_template pt on pp.product_tmpl_id = pt.id
					left join stock_move sm on sm.purchase_line_id = pl.id
					left join uom_uom um on um.id = pl.product_uom
                    where ((pl.product_qty * (1/um.factor)) * pt.net_weight) > 50
                    group by rp.ref, pl.partner_id, pt.categ_id, pl.order_id, po.date_order,
                    pl.product_qty, pt.net_weight, pl.price_subtotal, po.state, po.company_id,
					pp.id, pp.default_code, sm.date_expected, sm.weight, sm.product_qty,
					sm.price_unit, um.factor); """
        self.env.cr.execute(query)

