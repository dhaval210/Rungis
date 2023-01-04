# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time

from .common_valuation import TestPurchase


class TestFifoPrice(TestPurchase):

    def test_00_test_fifo(self):
        print("def test_00_test_fifo(self):")
        """ Test product cost price with fifo removal strategy."""

        self._load('account', 'test', 'account_minimal_test.xml')
        self._load('stock_account', 'test', 'stock_valuation_account.xml')

        product_cable_management_box = self.env['product.product'].create({
            'default_code': 'FIFO',
            'name': 'FIFO Ice Cream',
            'type': 'product',
            'categ_id': self.env.ref('product.product_category_1').id,
            'list_price': 100.0,
            'standard_price': 70.0,
            'uom_id': self.env.ref('uom.product_uom_unit').id,
            'uom_po_id': self.env.ref('uom.product_uom_unit').id,
            'cost_method': 'fifo',
            'valuation': 'real_time',
            'property_stock_account_input': self.ref('purchase.o_expense'),
            'property_stock_account_output': self.ref('purchase.o_income'),
            'supplier_taxes_id': '[]',
            'description': 'FIFO Ice Cream',
            'catch_weight_ok': True,
            'cw_uom_id':  self.env.ref('uom.product_uom_kgm').id,
            'purchase_price_base': 'cwuom',
        })

        purchase_order_1 = self.env['purchase.order'].create({
            'partner_id': self.env.ref('base.res_partner_3').id,
            'order_line': [(0, 0, {
                'name': 'FIFO Ice Cream',
                'product_id': product_cable_management_box.id,
                'product_qty': 10.0,
                'product_uom': self.env.ref('uom.product_uom_unit').id,
                'product_cw_uom_qty': 20,
                'product_cw_uom': self.env.ref('uom.product_uom_kgm').id,
                'price_unit': 50.0,
                'date_planned': time.strftime('%Y-%m-%d')})],
        })

        purchase_order_1.button_confirm()

        self.assertEquals(purchase_order_1.state, 'purchase')

        picking = purchase_order_1.picking_ids[0]
        self.env['stock.immediate.transfer'].create({'pick_ids': [(4, picking.id)]}).process()

        self.assertEquals(product_cable_management_box.standard_price, 70.0, 'Standard price should not have changed')
        self.assertEquals(product_cable_management_box.stock_value, 1000.0, 'Wrong stock value')

        purchase_order_2 = self.env['purchase.order'].create({
            'partner_id': self.env.ref('base.res_partner_3').id,
            'order_line': [(0, 0, {
                'name': 'FIFO Ice Cream',
                'product_id': product_cable_management_box.id,
                'product_qty': 20.0,
                'product_uom': self.env.ref('uom.product_uom_unit').id,
                'product_cw_uom_qty': 40,
                'product_cw_uom': self.env.ref('uom.product_uom_kgm').id,
                'price_unit': 80.0,
                'date_planned': time.strftime('%Y-%m-%d')})],
            })

        purchase_order_2.button_confirm()

        picking = purchase_order_2.picking_ids[0]
        self.env['stock.immediate.transfer'].create({'pick_ids': [(4, picking.id)]}).process()

        self.assertEquals(product_cable_management_box.standard_price, 70.0, 'Standard price as fifo price of second reception incorrect!')
        self.assertEquals(product_cable_management_box.stock_value, 4200.0, 'Stock valuation should be 2900')

        outgoing_shipment = self.env['stock.picking'].create({
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            'move_lines': [(0, 0, {
                'name': product_cable_management_box.name,
                'product_id': product_cable_management_box.id,
                'product_uom_qty': 20.0,
                'product_uom': self.env.ref('uom.product_uom_unit').id,
                'product_cw_uom_qty': 40,
                'product_cw_uom': self.env.ref('uom.product_uom_kgm').id,
                'location_id': self.env.ref('stock.stock_location_stock').id,
                'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                'picking_type_id': self.env.ref('stock.picking_type_out').id})]
            })

        outgoing_shipment.action_assign()

        self.env['stock.immediate.transfer'].create({'pick_ids': [(4, outgoing_shipment.id)]}).process()

        self.assertEqual(product_cable_management_box.stock_value, 1600.0, 'Stock valuation should be 1600')

        outgoing_shipment_uom = self.env['stock.picking'].create({
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            'move_lines': [(0, 0, {
                'name': product_cable_management_box.name,
                'product_id': product_cable_management_box.id,
                'product_uom_qty': 2,
                'product_uom': self.env.ref('uom.product_uom_unit').id,
                'product_cw_uom_qty': 1,
                'product_cw_uom': self.env.ref('uom.product_uom_kgm').id,
                'location_id': self.env.ref('stock.stock_location_stock').id,
                'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                'picking_type_id': self.env.ref('stock.picking_type_out').id})]
            })

        outgoing_shipment_uom.action_assign()

        self.env['stock.immediate.transfer'].create({'pick_ids': [(4, outgoing_shipment_uom.id)]}).process()
        print("product_cable_management_box.stock_value", product_cable_management_box.stock_value)
        self.assertEqual(product_cable_management_box.stock_value, 1560.0, 'Stock valuation should be 1560')
        self.assertEqual(product_cable_management_box.qty_available, 19.5, 'Should still have 19.5 in stock')
        self.assertEqual(product_cable_management_box.cw_qty_available, 19.5, 'Should still have 19.5 in stock')

