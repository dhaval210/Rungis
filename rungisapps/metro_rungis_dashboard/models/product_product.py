# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta


class ProductProduct(models.Model):
    _inherit = 'product.product'

    sub_category = fields.Char(string="Art. Group", related='categ_id.name')
    sale_order_amount = fields.Integer(string="Total Sale Amount", compute="get_product_data")
    stock_quantity = fields.Float(string="Stock Quantity", compute="get_product_data")
    stock_amount = fields.Float(string="Stock Amount", compute="get_product_data",
                                help="based on quantity available and sale price")
    average_sale_amount = fields.Float(string="Average Sale Amount", compute="get_product_data",
                                       help="total untaxed amount is divided by unique sale days")
    stock_days = fields.Float(string="Stock Days", compute="get_product_data",
                              help="stock amount is divided by avg sale amount")
    last_stock_date = fields.Datetime(string="Date of last stock incoming", compute="get_product_data")
    sale_ytd = fields.Integer(string="Sales in YTD", help="Total untaxed amount in a year")
    purchase_amount_12_per_month = fields.Float("Purchase amount in last 12 month per month",
                                                help="Purchase amount in last 12 month in each month average")
    purchase_amount_3 = fields.Float("Purchase Average amount in last 3 month",
                                     help="Average price in 3 months based on the quantity")
    purchase_amount_6 = fields.Float("Purchase Average amount in last 6 month",
                                     help="Average price in 6 months based on the quantity")
    purchase_amount_12 = fields.Float("Purchase Average amount in last 12 month",
                                      help="Average price in 12 months based on the quantity")
    product_purchase_rank = fields.Integer("Purchase Product Ranking",
                                           help="Purchase amount based on qty purchased")

    def get_product_data(self):

        sale_report_groups = self.env['sale.report'].read_group([('product_id', '=', self.ids), ('state', '=', 'sale')],
                                                                ['product_id', 'price_subtotal'], ['product_id'])
        for group in sale_report_groups:
            product = self.browse(group['product_id'][0])
            stock_quant_ids = product.stock_quant_ids.filtered(lambda s: s.quantity > 0 and
                                                                         s.location_id.usage == 'internal')
            incoming_dates = stock_quant_ids.mapped('in_date')
            min_date = False
            if incoming_dates:
                min_date = max(incoming_dates)
            product.last_stock_date = min_date
            order_lines = self.env['sale.order.line'].search([('product_id', '=', product.id), ('state', '=', 'sale')])
            sale_orders = order_lines.mapped('order_id')
            date_list = sale_orders.mapped('confirmation_date')
            sale_dates = [date.date() for date in date_list]
            sale_dates = set(sale_dates)
            count_dates = len(sale_dates)
            product.stock_quantity = product.qty_available
            untaxed_amount = group['price_subtotal']
            product.sale_order_amount = untaxed_amount
            if product.sale_price_base == 'uom':
                product.stock_amount = product.qty_available * product.lst_price
            else:
                product.stock_amount = product.cw_qty_available * product.lst_price
            product.average_sale_amount = untaxed_amount / count_dates if count_dates and untaxed_amount else 0
            if product.stock_amount > product.average_sale_amount != 0 and product.stock_amount != 0:
                product.stock_days = product.stock_amount / product.average_sale_amount

    @api.depends('sales_count')
    def get_article_details(self):
        today = datetime.today()
        year_before = today - relativedelta(months=12)
        last_3_month = today - relativedelta(months=3)
        last_6_month = today - relativedelta(months=6)
        domains = {'purchase_amount_12': [('date_order', '>=', year_before)],
                   'purchase_amount_3': [('date_order', '>=', last_3_month)],
                   'purchase_amount_6': [('date_order', '>=', last_6_month)]}
        products = self.search([])
        domain = [
            ('state', '=', 'sale'),
            ('product_id', 'in', products.ids),
            ('date', '>=', year_before),
        ]
        sale_record = self.env['sale.report'].read_group(domain, ['product_id', 'price_subtotal'], ['product_id'])
        for group in sale_record:
            product = self.browse(group['product_id'][0])
            product.sale_ytd = group['price_subtotal']
        ids = []
        for rec in domains:
            purchase_records = self.env['purchase.order.line'].read_group([('state', '=', 'purchase'),
                                                                           ('product_id', 'in', products.ids)] +
                                                                          domains[rec],['product_id', 'price_subtotal',
                                                                          'product_qty'], ['product_id'])
            sorted_list = sorted(purchase_records, key=lambda k: k['product_qty'], reverse=True)
            i = 1
            for group in sorted_list:
                group.update(rank=i)
                product = self.browse(group['product_id'][0])
                if rec == 'purchase_amount_12':
                    product.purchase_amount_12_per_month = group['price_subtotal'] / 12
                product[rec] = group['price_subtotal'] / group['product_qty'] if group['product_qty'] else 0
                if product.purchase_amount_12_per_month > 0:
                    product['product_purchase_rank'] = group['rank']
                    ids.append(product.id)
                    i += 1
