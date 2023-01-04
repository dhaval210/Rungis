# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools


class BuyingReorders(models.Model):
    _name = 'buying.reorders'
    _auto = False
    _description = 'Buying Reorders'
    _rec_name = 'user_id'

    user_id = fields.Many2one('res.users', "Users", readonly=True)
    no_purchase = fields.Integer("Number Of Purchase", readonly=True)
    category_id = fields.Many2one('product.category', "Category", readonly=True)
    subtotal = fields.Float("Purchase Amount", readonly=True)
    company_id = fields.Many2one('res.company', "Company", readonly=True)
    currency_id = fields.Many2one('res.currency', "Currency", readonly=True)
    purchase_percentage = fields.Float('Purchase Percentage on Total Amount', compute="get_percentage")

    @api.depends('no_purchase')
    def get_percentage(self):
        purchase_ids = self.env['purchase.order'].search([('state', '=', 'purchase')])
        list_amounts = purchase_ids.mapped('amount_untaxed')
        total_amount = sum(list_amounts)
        for recd in self:
            amount_percentage = round(100.0 * recd.subtotal / total_amount, 2) * 100
            recd.purchase_percentage = amount_percentage

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """ CREATE or REPLACE VIEW buying_reorders AS (select row_number() OVER () as id,ru.id as user_id, 
                    count(DISTINCT po.id) as no_purchase, pt.categ_id as category_id, 
                    sum(pl.price_subtotal) as subtotal, po.company_id as company_id, 
                    po.currency_id as currency_id from res_users as ru
                    left join purchase_order po on po.user_id = ru.id
                    left join purchase_order_line pl on po.id = pl.order_id
                    left join product_product pp on pp.id = pl.product_id
                    left join product_template pt on pt.id = pp.product_tmpl_id
                    where ru.active = true and po.name ilike 'PO5%' and po.state = 'purchase'
                    group by ru.id, pt.categ_id, po.company_id, po.currency_id); """
        self.env.cr.execute(query)
