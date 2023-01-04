from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    customer_number = fields.Char(string='Customer Number', related='partner_id.ref')
    customer_ranking = fields.Integer(string='Customer Ranking', related='partner_id.customer_ranking',
                                      help="Based on the sale order count")

