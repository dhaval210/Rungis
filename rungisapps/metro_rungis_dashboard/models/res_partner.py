# -*- coding: utf-8 -*
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from datetime import datetime, timedelta


class ResPartner(models.Model):
    _inherit = 'res.partner'

    customer_ranking = fields.Integer(string="Customer Ranking",
                                      help="Based on count of sale order")
    purchase_ranking = fields.Integer(string="Purchase Ranking",
                                      help="Based on count of purchase order")
    purchase_amount_last_1_month = fields.Float(string="Purchase Amount for Last Calendar Month",
                                           help="Based on date of order which having 1 month before")
    purchase_amount_last_6 = fields.Float(string="Purchase Amount last 6 Month/Month",
                                          help="Based on date of order which having 6 month before and "
                                               "based on each month")
    purchase_amount_average_last_6 = fields.Float(string="Purchase Amount Average for Last 6 month",
                                           help="Average purchase amount in all the records for last 6 month")
    product_count = fields.Integer(string="Product Count", compute="get_product_count",
                                   help="based total product count for particular partner")

    def get_all_details(self):
        self.get_customer_rank()
        self.get_purchase_rank()
        self.get_purchase_details()

    @api.depends('sale_order_ids')
    def get_customer_rank(self):
        customer_ids = self.with_context(active_test=False).search([('sale_order_ids', '!=', False)])
        before_6_month = datetime.today() - relativedelta(months=6)
        sale_order_groups = self.env['sale.order'].read_group(
            domain=[('partner_id', 'in', customer_ids.ids), ('state', '=', 'sale'),
                    ('amount_untaxed', '<=', 150), ('amount_untaxed', '>=', 1),
                    ('expected_date', '>=', before_6_month)],
            fields=['partner_id', 'amount_untaxed'], groupby=['partner_id']
        )
        sorted_list = sorted(sale_order_groups, key=lambda k: k['amount_untaxed'], reverse=True)
        i = 0
        for recd in sorted_list:
            i += 1
            recd.update(rank=i)
            partner = self.browse(recd['partner_id'][0])
            if partner:
                partner.customer_ranking = recd['rank']

    @api.depends('purchase_order_count')
    def get_purchase_rank(self):
        customer_ids = self.with_context(active_test=False).search([('purchase_order_count', '>', 0)])
        before_6_month = datetime.today() - relativedelta(months=6)
        purchase_order_groups = self.env['purchase.order'].read_group(
            domain=[('partner_id', 'in', customer_ids.ids), ('state', '=', 'purchase'),
                    ('amount_untaxed', '<=', 250), ('amount_untaxed', '>=', 1),
                    ('po_date_planned', '>=', before_6_month)],
            fields=['partner_id', 'amount_untaxed'], groupby=['partner_id']
        )
        sorted_list = sorted(purchase_order_groups, key=lambda k: k['amount_untaxed'], reverse=True)
        i = 0
        for recd in sorted_list:
            i += 1
            recd.update(rank=i)
            partner = self.browse(recd['partner_id'][0])
            if partner:
                partner.purchase_ranking = recd['rank']

    @api.depends('purchase_order_count')
    def get_purchase_details(self):
        supplier_ids = self.with_context(active_test=False).search([])
        today = datetime.today()
        before_30_day = datetime.today() - relativedelta(months=1)
        last_month_start = datetime(before_30_day.year, before_30_day.month, 1, 00, 00, 00)
        current_month_start = datetime(today.year, today.month, 1, 00, 00, 00)
        before_6_month = datetime.today() - relativedelta(months=6)
        last_6_month_start = datetime(before_6_month.year, before_6_month.month, 1, 00, 00, 00)
        domains = {
            'purchase_amount_last_1_month': [('date_order', '<', current_month_start), ('date_order', '>=', last_month_start)],
            'purchase_amount_last_6': [('date_order', '<', current_month_start), ('date_order', '>=', last_6_month_start)],
            'purchase_amount_average_last_6': [('date_order', '<', current_month_start), ('date_order', '>=', last_6_month_start)]
        }
        for field in domains:
            purchase_order_groups = self.env['purchase.order'].read_group(
                domain=[('partner_id', 'in', supplier_ids.ids), ('state', '=', 'purchase')] + domains[field],
                fields=['partner_id', 'amount_untaxed'], groupby=['partner_id']
            )
            for recd in purchase_order_groups:
                partner = self.browse(recd['partner_id'][0])
                amount = recd['amount_untaxed']
                if field == 'purchase_amount_last_6':
                    amount = amount / 6
                if field == 'purchase_amount_average_last_6':
                    amount = amount / recd['partner_id_count']
                if partner:
                    partner[field] = amount

    @api.depends('purchase_order_count')
    def get_product_count(self):
        partners = self.filtered(lambda p: p.purchase_order_count >= 1 and p.supplier)
        for recd in partners:
            purchase_ids = self.env['purchase.order'].search([('partner_id', '=', recd.id), ('state', '=', 'purchase')])
            order_lines = purchase_ids.mapped('order_line')
            products = order_lines.mapped('product_id')
            recd.product_count = len(products)
