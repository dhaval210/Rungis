# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestOnchangeProductIdCwAvgQty(TransactionCase):
    """Test that when an included tax is mapped by a fiscal position, the included tax must be
    subtracted to the price of the product.
    """

    def setUp(self):
        super(TestOnchangeProductIdCwAvgQty, self).setUp()
        self.fiscal_position_model = self.env['account.fiscal.position']
        self.fiscal_position_tax_model = self.env['account.fiscal.position.tax']
        self.tax_model = self.env['account.tax']
        self.so_model = self.env['sale.order']
        self.po_line_model = self.env['sale.order.line']
        self.res_partner_model = self.env['res.partner']
        self.product_tmpl_model = self.env['product.template']
        self.product_model = self.env['product.product']
        self.product_uom_model = self.env['uom.uom']
        self.supplierinfo_model = self.env["product.supplierinfo"]
        self.pricelist_model = self.env['product.pricelist']
        self.env.user.write({'groups_id': [(4, self.env.ref('tis_catch_weight.group_catch_weight').id)]})

    def test_onchange_product_id(self):
        uom_id = self.product_uom_model.search([('name', '=', 'Units')])[0]
        cw_uom_id = self.product_uom_model.search([('name', '=', 'kg')])[0]
        pricelist = self.pricelist_model.search([('name', '=', 'Public Pricelist')])[0]

        partner_id = self.res_partner_model.create(dict(name="George"))
        tax_include_id = self.tax_model.create(dict(name="Include tax",
                                                    amount='21.00',
                                                    price_include=True,
                                                    type_tax_use='sale'))
        tax_exclude_id = self.tax_model.create(dict(name="Exclude tax",
                                                    amount='0.00',
                                                    type_tax_use='sale'))

        product_tmpl_id = self.product_tmpl_model.create(dict(name="Carton of Apple",
                                                              list_price=121,
                                                              catch_weight_ok=True,
                                                              average_cw_quantity=1.5,
                                                              cw_uom_id=cw_uom_id.id,
                                                              taxes_id=[(6, 0, [tax_include_id.id])]))

        product_id = product_tmpl_id.product_variant_id
        product_id.catch_weight_ok = True
        product_id.average_cw_quantity = 1.5

        fp_id = self.fiscal_position_model.create(dict(name="fiscal position", sequence=1))

        fp_tax_id = self.fiscal_position_tax_model.create(dict(position_id=fp_id.id,
                                                               tax_src_id=tax_include_id.id,
                                                               tax_dest_id=tax_exclude_id.id))

        order_form = Form(self.env['sale.order'].with_context(tracking_disable=True))
        order_form.partner_id = partner_id
        order_form.pricelist_id = pricelist
        order_form.fiscal_position_id = fp_id
        with order_form.order_line.new() as line:
            line.name = product_id.name
            line.product_id = product_id
            line.product_uom_qty = 2.0
            line.product_uom = uom_id
            line.product_cw_uom = cw_uom_id
        sale_order = order_form.save()

        order_form = Form(self.env['purchase.order'].with_context(tracking_disable=True))
        order_form.partner_id = partner_id
        order_form.fiscal_position_id = fp_id
        with order_form.order_line.new() as line:
            line.name = product_id.name
            line.product_id = product_id
            line.product_qty = 2.0
            line.product_uom = uom_id
            line.product_cw_uom = cw_uom_id
        purchase_order = order_form.save()

        self.assertEquals(3, sale_order.order_line[0].product_cw_uom_qty, "Wrong Catchweight quantity")
        for line in sale_order.order_line:
            line.product_uom_qty = 4.0
            line.product_uom_change()
        self.assertEquals(6, sale_order.order_line[0].product_cw_uom_qty, "Wrong Catchweight quantity")
        self.assertEquals(3, purchase_order.order_line[0].product_cw_uom_qty, "Wrong Catchweight quantity")
        for line in purchase_order.order_line:
            line.product_qty = 4.0
            line._onchange_quantity()
        self.assertEquals(6, purchase_order.order_line[0].product_cw_uom_qty, "Wrong Catchweight quantity")

    def setup_company_data(self, company_name, **kwargs):
        ''' Create a new company having the name passed as parameter.
        A chart of accounts will be installed to this company: the same as the current company one.
        The current user will get access to this company.

        :param company_name: The name of the company.
        :return: A dictionary will be returned containing all relevant accounting data for testing.
        '''
        chart_template = self.env.user.company_id.chart_template_id
        company = self.env['res.company'].create({
            'name': company_name,
            'currency_id': self.env.user.company_id.currency_id.id,
            **kwargs,
        })
        self.env.user.company_ids |= company
        self.env.user.company_id = company

        chart_template = self.env['account.chart.template'].browse(chart_template.id)
        chart_template.try_loading()

        company.write({'currency_id': kwargs.get('currency_id', self.env.user.company_id.currency_id.id)})

        return {
            'company': company,
            'currency': company.currency_id,
            'default_account_revenue': self.env['account.account'].search([
                ('company_id', '=', company.id),
                ('user_type_id', '=', self.env.ref('account.data_account_type_revenue').id)
            ], limit=1),
            'default_account_expense': self.env['account.account'].search([
                ('company_id', '=', company.id),
                ('user_type_id', '=', self.env.ref('account.data_account_type_expenses').id)
            ], limit=1),
            'default_account_receivable': self.env['account.account'].search([
                ('company_id', '=', company.id),
                ('user_type_id.type', '=', 'receivable')
            ], limit=1),
            'default_account_payable': self.env['account.account'].search([
                ('company_id', '=', company.id),
                ('user_type_id.type', '=', 'payable')
            ], limit=1),
            'default_account_tax_sale': company.account_sale_tax_id.mapped('invoice_repartition_line_ids.account_id'),
            'default_account_tax_purchase': company.account_purchase_tax_id.mapped(
                'invoice_repartition_line_ids.account_id'),
            'default_journal_misc': self.env['account.journal'].search([
                ('company_id', '=', company.id),
                ('type', '=', 'general')
            ], limit=1),
            'default_journal_sale': self.env['account.journal'].search([
                ('company_id', '=', company.id),
                ('type', '=', 'sale')
            ], limit=1),
            'default_journal_purchase': self.env['account.journal'].search([
                ('company_id', '=', company.id),
                ('type', '=', 'purchase')
            ], limit=1),
            'default_journal_bank': self.env['account.journal'].search([
                ('company_id', '=', company.id),
                ('type', '=', 'bank')
            ], limit=1),
            'default_journal_cash': self.env['account.journal'].search([
                ('company_id', '=', company.id),
                ('type', '=', 'cash')
            ], limit=1),
            'default_tax_sale': company.account_sale_tax_id,
            'default_tax_purchase': company.account_purchase_tax_id,
        }

