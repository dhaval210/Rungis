"""License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)."""

from datetime import datetime, timedelta
from odoo import models, api, fields


class CustomerStatus(models.Model):
    """inherit base for get customer for adding boolean"""
    _inherit = 'res.partner'

    new_customer = fields.Boolean(string='New Customer',
                                  compute='get_order_date',
                                  search='search_new_customer')

    lost_customer = fields.Boolean(string='Lost Customer',
                                   compute='get_lost_customer',
                                   search='search_lost_customer')

    buy_customer = fields.Boolean(compute='get_buy_customer',
                                  string='Buying Customer',
                                  search='search_buy_customer')

    @api.multi
    def get_order_date(self):
        """select first order date using query"""
        for contact in self:
            query = """SELECT confirmation_date as first_order FROM sale_order
            WHERE partner_id = %s AND confirmation_date IS NOT NULL ORDER BY 
            confirmation_date ASC LIMIT 1"""
            contact._cr.execute(query, [contact.id])
            record = contact._cr.dictfetchall()
            if record:
                first_date_str = str(record[0]['first_order']).split('.')[0]
                today = datetime.today()
                first_date = datetime.strptime(str(first_date_str),
                                               '%Y-%m-%d %H:%M:%S')
                if first_date.month + 1 <= today.month:
                    if first_date.year == today.year:
                        contact.new_customer = False
                else:
                    contact.new_customer = True

    @api.multi
    def search_new_customer(self, operator, value):
        """add new customer to filter"""
        return [('id', 'in', [x.id for x in self.search([]) if
                              x.new_customer])]

    @api.multi
    def get_buy_customer(self):
        """select first order date using query"""
        for contact in self:
            date_180 = datetime.today() - timedelta(days=180)
            date_90 = datetime.today() - timedelta(days=90)

            last_order = """SELECT confirmation_date FROM sale_order  WHERE partner_id
                                    = %s AND confirmation_date >= %s
                                    ORDER BY confirmation_date DESC
                                    LIMIT 1"""
            contact._cr.execute(last_order, [contact.id, date_90])
            last_order2 = contact._cr.dictfetchall()
            if last_order2:
                query = """SELECT so.name FROM sale_order so WHERE partner_id = %s
                                    AND confirmation_date >= %s"""
                contact._cr.execute(query, [contact.id, date_180])
                order_count = len(contact._cr.dictfetchall())
                contact.buy_customer = True if order_count >= 6 else False
            else:
                contact.buy_customer = False


    @api.multi
    def search_buy_customer(self, operator, value):
        """add new customer to filter"""
        return [('id', 'in', [x.id for x in self.search([]) if
                              x.buy_customer])]

    @api.multi
    def get_lost_customer(self):
        """select first order date using query"""

        list_date = []
        for contact in self:
            query = """SELECT confirmation_date as total_order FROM sale_order
            WHERE partner_id = %s AND  confirmation_date IS NOT NULL ORDER BY 
            confirmation_date DESC"""
            contact._cr.execute(query, [contact.id])
            record = contact._cr.dictfetchall()
            if record:
                for rec in record:
                    list_date.append(rec['total_order'])

                def days_diff(a, b):
                    if a and b:
                        split_a = str(a).split('.')[0]
                        split_b = str(b).split('.')[0]
                        return (datetime.strptime(split_a, '%Y-%m-%d '
                                                           '%H:%M:%S') -
                                datetime.strptime(split_b, '%Y-%m-%d ' 
                                                           '%H:%M:%S')).days
                if len(list_date) - 1:
                    average = sum(
                        days_diff(a, b) for a, b in zip(list_date, list_date[1:])) \
                              / (len(list_date) - 1)
                    today_date = datetime.now().date()
                    query = """SELECT confirmation_date as last_order FROM  
                    sale_order WHERE partner_id = %s AND confirmation_date IS NOT NULL ORDER BY 
                    confirmation_date DESC LIMIT 1 """
                    contact._cr.execute(query, [contact.id])
                    record = contact._cr.dictfetchall()
                    if record and not contact.new_customer:
                        date = datetime.strptime(str(record[0]['last_order']),
                                                 '%Y-%m-%d %H:%M:%S')
                        date_difference = 2 * (today_date - date.date()).days
                        if average <= date_difference:
                            contact.lost_customer = True
                        else:
                            contact.lost_customer = False

    @api.multi
    def search_lost_customer(self, operator, value):
        """add new customer to filter"""

        return [('id', 'in', [x.id for x in self.search([]) if
                              x.lost_customer])]
