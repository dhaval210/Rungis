"""License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)."""

from odoo import models, api, fields


class SaleFilter(models.Model):
    """inherit sale order for adding filter """
    _inherit = 'sale.order'

    new_customer_inherited = fields.Boolean(string='New Customer',
                                            related='partner_id.new_customer')
    lost_customer_inherited = fields.Boolean(string='Lost Customer',
                                             related='partner_id.lost_customer')
    buy_customer_inherited = fields.Boolean(string='Buying Customer',
                                            related='partner_id.buy_customer')


class InvoiceFilter(models.Model):
    """inherit account invoice for adding filter"""
    _inherit = 'account.invoice'

    new_customer_inherit = fields.Boolean(string='New Customer',
                                          related='partner_id.new_customer')
    lost_customer_inherit = fields.Boolean(string='Lost Customer',
                                           related='partner_id.lost_customer')
    buy_customer_inherit = fields.Boolean(string='Lost Customer',
                                          related='partner_id.buy_customer')
