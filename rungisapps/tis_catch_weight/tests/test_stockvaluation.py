# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime
from unittest.mock import patch

from odoo import fields
from odoo.tests import Form
from odoo.tests.common import TransactionCase, tagged
from odoo.addons.account.tests.account_test_classes import AccountingTestCase
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class TestStockValuation(TransactionCase):
    def setUp(self):
        print("TestStockValuation(TransactionCase):")
        super(TestStockValuation, self).setUp()
        self.supplier_location = self.env.ref('stock.stock_location_suppliers')
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.partner_id = self.env.ref('base.res_partner_1')
        self.product1 = self.env.ref('product.product_product_8')
        self.product1.catch_weight_ok = True
        self. cw_uom_id = self.env['uom.uom'].search([('name', '=', 'kg')])[0]
        self.product1.cw_uom_id = self.cw_uom_id.id

        Account = self.env['account.account']
        self.stock_input_account = Account.create({
            'name': 'Stock Input',
            'code': 'StockIn',
            'user_type_id': self.env.ref('account.data_account_type_current_assets').id,
            'reconcile': True,
        })
        self.stock_output_account = Account.create({
            'name': 'Stock Output',
            'code': 'StockOut',
            'user_type_id': self.env.ref('account.data_account_type_current_assets').id,
            'reconcile': True,
        })
        self.stock_valuation_account = Account.create({
            'name': 'Stock Valuation',
            'code': 'Stock Valuation',
            'user_type_id': self.env.ref('account.data_account_type_current_assets').id,
        })
        self.stock_journal = self.env['account.journal'].create({
            'name': 'Stock Journal',
            'code': 'STJTEST',
            'type': 'general',
        })
        self.product1.categ_id.write({
            'property_stock_account_input_categ_id': self.stock_input_account.id,
            'property_stock_account_output_categ_id': self.stock_output_account.id,
            'property_stock_valuation_account_id': self.stock_valuation_account.id,
            'property_stock_journal': self.stock_journal.id,
            'sale_price_base': 'cwuom',
            'purchase_price_base': 'cwuom'

        })

    def test_output_category_CW_UOM(self):
        """Check what will be the output if saleprice base is set on Product caegory"""
        base = self.product1._is_price_based_on_cw('sale')
        self.assertTrue(base)
        purchase_base = self.product1._is_price_based_on_cw('purchase')
        self.assertTrue(purchase_base)

    def test_change_unit_cost_average_1(self):
        """ Confirm a purchase order and create the associated receipt, change the unit cost of the
        purchase order before validating the receipt, the value of the received goods should be set
        according to the last unit cost.
        """
        self.product1.product_tmpl_id.cost_method = 'average'
        po1 = self.env['purchase.order'].create({
            'partner_id': self.partner_id.id,
            'order_line': [
                (0, 0, {
                    'name': self.product1.name,
                    'product_id': self.product1.id,
                    'product_qty': 10.0,
                    'product_cw_uom_qty': 20.0,
                    'product_uom': self.product1.uom_po_id.id,
                    'product_cw_uom': self.cw_uom_id.id,
                    'price_unit': 100.0,
                    'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                }),
            ],
        })
        po1.button_confirm()

        picking1 = po1.picking_ids[0]
        move1 = picking1.move_lines[0]

        self.assertEquals(move1.price_unit, 100)

        po1.order_line.price_unit = 200

        self.assertEquals(move1.price_unit, 100)

        res_dict = picking1.button_validate()
        wizard = self.env[(res_dict.get('res_model'))].browse(res_dict.get('res_id'))
        wizard.process()

        self.assertEquals(move1.price_unit, 200)

        self.assertEquals(self.product1.stock_value, 4000)

    def test_standard_price_change_1(self):
        """ Confirm a purchase order and create the associated receipt, change the unit cost of the
        purchase order and the standard price of the product before validating the receipt, the
        value of the received goods should be set according to the last standard price.
        """
        self.product1.product_tmpl_id.cost_method = 'standard'

        self.product1.product_tmpl_id.standard_price = 10

        po1 = self.env['purchase.order'].create({
            'partner_id': self.partner_id.id,
            'order_line': [
                (0, 0, {
                    'name': self.product1.name,
                    'product_id': self.product1.id,
                    'product_qty': 10.0,
                    'product_cw_uom_qty': 20.0,
                    'product_uom': self.product1.uom_po_id.id,
                    'product_cw_uom': self.cw_uom_id.id,
                    'price_unit': 11.0,
                    'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                }),
            ],
        })
        po1.button_confirm()

        picking1 = po1.picking_ids[0]
        move1 = picking1.move_lines[0]

        self.assertEquals(move1.price_unit, 11)

        self.product1.product_tmpl_id.standard_price = 12

        self.assertEquals(move1.price_unit, 11)

        res_dict = picking1.button_validate()
        wizard = self.env[(res_dict.get('res_model'))].browse(res_dict.get('res_id'))
        wizard.process()

        self.assertEquals(move1.price_unit, 12)


        self.assertEquals(self.product1.stock_value, 240)

    def test_change_currency_rate_average_1(self):
        """ Confirm a purchase order in another currency and create the associated receipt, change
        the currency rate, validate the receipt and then check that the value of the received goods
        is set according to the last currency rate.
        """
        self.env['res.currency.rate'].search([]).unlink()
        usd_currency = self.env.ref('base.USD')
        self.env.user.company_id.currency_id = usd_currency.id

        eur_currency = self.env.ref('base.EUR')

        self.product1.product_tmpl_id.cost_method = 'average'

        po1 = self.env['purchase.order'].create({
            'partner_id': self.partner_id.id,
            'currency_id': eur_currency.id,
            'order_line': [
                (0, 0, {
                    'name': self.product1.name,
                    'product_id': self.product1.id,
                    'product_qty': 10.0,
                    'product_cw_uom_qty': 20.0,
                    'product_uom': self.product1.uom_po_id.id,
                    'product_cw_uom': self.cw_uom_id.id,
                    'price_unit': 100.0,
                    'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                }),
            ],
        })
        po1.button_confirm()

        picking1 = po1.picking_ids[0]
        move1 = picking1.move_lines[0]

        price_unit_usd = po1.currency_id._convert(
            po1.order_line.price_unit, po1.company_id.currency_id,
            self.env.user.company_id, fields.Date.today(), round=False)
        print("price_unit_usd", price_unit_usd)
        print("self.env.user.company_id.currency_id", self.env.user.company_id.currency_id)

        self.assertAlmostEqual(move1.price_unit, price_unit_usd, places=2)

        self.env['res.currency.rate'].create({
            'name': time.strftime('%Y-%m-%d'),
            'rate': 2.0,
            'currency_id': eur_currency.id,
            'company_id': po1.company_id.id,
        })
        eur_currency._compute_current_rate()
        price_unit_usd_new_rate = po1.currency_id._convert(
            po1.order_line.price_unit, po1.company_id.currency_id,
            self.env.user.company_id, fields.Date.today(), round=False)
        print("price_unit_usd_new_rate", price_unit_usd_new_rate)

        print("NEW CURRENCY", self.env.user.company_id.currency_id)

        self.assertLess(price_unit_usd_new_rate, price_unit_usd)

        self.assertAlmostEqual(move1.price_unit, price_unit_usd, places=2)

        res_dict = picking1.button_validate()
        wizard = self.env[(res_dict.get('res_model'))].browse(res_dict.get('res_id'))
        wizard.process()

        self.assertAlmostEqual(move1.price_unit, price_unit_usd_new_rate)

        self.assertAlmostEqual(self.product1.stock_value, price_unit_usd_new_rate * self.product1.product_cw_uom_qty, delta=0.1)

    def test_extra_move_fifo_1(self):
        """ Check that the extra move when over processing a receipt is correctly merged back in
        the original move.
        """
        self.product1.product_tmpl_id.cost_method = 'fifo'
        po1 = self.env['purchase.order'].create({
            'partner_id': self.partner_id.id,
            'order_line': [
                (0, 0, {
                    'name': self.product1.name,
                    'product_id': self.product1.id,
                    'product_qty': 10.0,
                    'product_cw_uom_qty': 20.0,
                    'product_uom': self.product1.uom_po_id.id,
                    'product_cw_uom': self.cw_uom_id.id,
                    'price_unit': 100.0,
                    'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                }),
            ],
        })
        po1.button_confirm()

        picking1 = po1.picking_ids[0]
        move1 = picking1.move_lines[0]
        move1.quantity_done = 15
        move1.cw_qty_done = 20
        res_dict = picking1.button_validate()
        self.assertEqual(res_dict['res_model'], 'stock.overprocessed.transfer')
        wizard = self.env[(res_dict.get('res_model'))].browse(res_dict.get('res_id'))
        wizard.action_confirm()

        self.assertEqual(len(picking1.move_lines), 1)
        self.assertEqual(move1.price_unit, 100)
        self.assertEqual(move1.product_qty, 15)
        self.assertEqual(self.product1.stock_value, 2000)

    def test_extra_move_fifo_2(self):
        print("test_extra_move_fifo_2")
        """ Check that the extra move when over processing a receipt is correctly merged back in
        the original move.
        """

        self.product1.product_tmpl_id.cost_method = 'fifo'
        po1 = self.env['purchase.order'].create({
            'partner_id': self.partner_id.id,
            'order_line': [
                (0, 0, {
                    'name': self.product1.name,
                    'product_id': self.product1.id,
                    'product_qty': 10.0,
                    'product_cw_uom_qty': 20.0,
                    'product_uom': self.product1.uom_po_id.id,
                    'product_cw_uom': self.cw_uom_id.id,
                    'price_unit': 100.0,
                    'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                }),
            ],
        })
        po1.button_confirm()

        picking1 = po1.picking_ids[0]
        move1 = picking1.move_lines[0]
        move1.quantity_done = 10
        move1.cw_qty_done = 30
        res_dict = picking1.button_validate()
        self.assertEqual(res_dict['res_model'], 'stock.overprocessed.transfer')
        wizard = self.env[(res_dict.get('res_model'))].browse(res_dict.get('res_id'))
        wizard.action_confirm()

        self.assertEqual(len(picking1.move_lines), 1)
        self.assertEqual(move1.price_unit, 100)
        self.assertEqual(move1.product_qty, 20)
        self.assertEqual(move1.product_cw_uom_qty, 30)
        self.assertEqual(self.product1.stock_value, 3000)

    def test_backorder_fifo_1(self):
        """ Check that the backordered move when under processing a receipt correctly keep the
        price unit of the original move.
        """

        self.product1.product_tmpl_id.cost_method = 'fifo'
        po1 = self.env['purchase.order'].create({
            'partner_id': self.partner_id.id,
            'order_line': [
                (0, 0, {
                    'name': self.product1.name,
                    'product_id': self.product1.id,
                    'product_qty': 10.0,
                    'product_cw_uom_qty': 20.0,
                    'product_uom': self.product1.uom_po_id.id,
                    'product_cw_uom': self.cw_uom_id.id,
                    'price_unit': 100.0,
                    'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                }),
            ],
        })
        po1.button_confirm()

        picking1 = po1.picking_ids[0]
        move1 = picking1.move_lines[0]
        move1.quantity_done = 5
        move1.cw_qty_done = 10
        res_dict = picking1.button_validate()
        self.assertEqual(res_dict['res_model'], 'stock.backorder.confirmation')
        wizard = self.env[(res_dict.get('res_model'))].browse(res_dict.get('res_id'))
        wizard.process()

        self.assertEqual(len(picking1.move_lines), 1)
        self.assertEqual(move1.price_unit, 100)
        self.assertEqual(move1.product_qty, 5)
        self.assertEqual(move1.product_cw_uom_qty, 10)

        picking2 = po1.picking_ids.filtered(lambda p: p.backorder_id)
        move2 = picking2.move_lines[0]
        self.assertEqual(len(picking2.move_lines), 1)
        self.assertEqual(move2.price_unit, 100)
        self.assertEqual(move2.product_qty, 5)
        self.assertEqual(move1.product_cw_uom_qty, 10)


