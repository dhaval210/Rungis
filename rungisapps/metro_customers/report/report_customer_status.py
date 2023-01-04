"""License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)."""
from odoo import models, fields, api


class ReportCustomers(models.AbstractModel):
    """for the pdf report"""

    _name = 'report.metro_customers.report_customer_status'

    def get_status(self, docs):
        """fetch the data from res partner"""

        customer = []
        if docs.check_customer_status == 'new_customer':
            rec = self.env['res.partner'].search([('new_customer', '=', True)])
            for status in rec:
                customer.append(status.name)
        if docs.check_customer_status == 'buy_customer':
            rec = self.env['res.partner'].search([('buy_customer', '=', True)])
            for status in rec:
                customer.append(status.name)
        if docs.check_customer_status == 'lost_customer':
            rec = self.env['res.partner'].search(
                [('lost_customer', '=', True)])
            for status in rec:
                customer.append(status.name)
        return [customer, docs.check_customer_status]

    @api.model
    def _get_report_values(self, docids, data=None):
        """calling default function for getting report"""

        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        customer = self.get_status(docs)[0]
        type = self.get_status(docs)[1]
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
            'customer': customer,
            'type': type,
        }

