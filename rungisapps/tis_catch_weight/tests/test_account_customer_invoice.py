from unittest.mock import patch

from odoo.addons.account.tests.account_test_users import AccountTestUsers
import datetime
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestAccountCustomerInvoice(AccountTestUsers):

    def test_customer_invoice(self):
        self.res_partner_bank_0 = self.env['res.partner.bank'].sudo(self.account_manager.id).create(dict(
            acc_type='bank',
            company_id=self.main_company.id,
            partner_id=self.main_partner.id,
            acc_number='123456789',
            bank_id=self.main_bank.id,
        ))

        self.account_invoice_obj = self.env['account.invoice']
        self.payment_term = self.env.ref('account.account_payment_term_advance')
        self.journalrec = self.env['account.journal'].search([('type', '=', 'sale')])[0]
        self.partner3 = self.env.ref('base.res_partner_3')
        account_user_type = self.env.ref('account.data_account_type_receivable')
        self.ova = self.env['account.account'].search([('user_type_id', '=', self.env.ref('account.data_account_type_current_assets').id)], limit=1)

        self.account_rec1_id = self.account_model.sudo(self.account_manager.id).create(dict(
            code="cust_acc",
            name="customer account",
            user_type_id=account_user_type.id,
            reconcile=True,
        ))

        uom_unit = self.env.ref('uom.product_uom_unit')
        cw_uom_id = self.env['uom.uom'].search([('name', '=', 'kg')])[0]
        user_type_income = self.env.ref('account.data_account_type_direct_costs')
        self.account_income_product = self.env['account.account'].create({
            'code': 'INCOME_PROD111',
            'name': 'Icome - Test Account',
            'user_type_id': user_type_income.id,
        })

        self.product_category = self.env['product.category'].create({
            'name': 'Product Category with Income account',
            'property_account_income_categ_id': self.account_income_product.id
        })
        self.product_order = self.env['product.product'].create({
            'name': "Zed+ Antivirus",
            'standard_price': 235.0,
            'list_price': 280.0,
            'type': 'consu',
            'catch_weight_ok': True,
            'sale_price_base': 'cwuom',
            'cw_uom_id': cw_uom_id.id,
            'uom_id': uom_unit.id,
            'uom_po_id': uom_unit.id,
            'invoice_policy': 'order',
            'expense_policy': 'no',
            'default_code': 'PROD_ORDER',
            'service_type': 'manual',
            'taxes_id': False,
            'categ_id': self.product_category.id,
        })

        invoice_line_data = [
            (0, 0,
                {
                    'product_id': self.product_order.id,
                    'quantity': 10.0,
                    'product_cw_uom_qty': 20.0,
                    'account_id': self.env['account.account'].search([('user_type_id', '=', self.env.ref('account.data_account_type_revenue').id)], limit=1).id,
                    'name': 'product test 5',
                    'price_unit': 100.00,
                }
             )
        ]

        self.account_invoice_customer0 = self.account_invoice_obj.sudo(self.account_user.id).create(dict(
            name="Test Customer Invoice",
            payment_term_id=self.payment_term.id,
            journal_id=self.journalrec.id,
            partner_id=self.partner3.id,
            account_id=self.account_rec1_id.id,
            invoice_line_ids=invoice_line_data
        ))

        invoice_tax_line = {
            'name': 'Test Tax for Customer Invoice',
            'manual': 1,
            'amount': 9050,
            'account_id': self.ova.id,
            'invoice_id': self.account_invoice_customer0.id,
        }
        tax = self.env['account.invoice.tax'].create(invoice_tax_line)

