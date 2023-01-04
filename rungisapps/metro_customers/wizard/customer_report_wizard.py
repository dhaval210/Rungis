"""License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)."""
from odoo import models, fields


class WizardViewCustomer(models.TransientModel):
    """create a new model for the wizard view"""
    _name = 'customer.wizard'

    check_customer_status = fields.Selection([
        ('new_customer', 'New Customer'),
        ('buy_customer', 'Buying Customer'),
        ('lost_customer', 'Lost Customer')
    ], string='Status', required=True, default='new_customer')

    def print_button(self, data):
        """Redirects to the report with the values obtained from the wizard
        'data['form']': name of check_customer_status """

        data = {}
        data['form'] = self.read(['check_customer_status'])
        print("jdjd",data)
        return self.env.ref('metro_customers.action_report_list_report'). \
            report_action(self, data=data)


