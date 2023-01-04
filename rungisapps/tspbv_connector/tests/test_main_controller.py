from psycopg2 import IntegrityError
from mock import patch
from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from ..controllers.main import TspbvController


class FakeRequest(object):
    def __init__(self, env):
        self.env = env

    def make_response(self, data, headers):
        return FakeResponse(data, headers)


class FakeResponse(object):
    def __init__(self, data, headers):
        self.data = data
        self.headers = dict(headers)


class TestController(TransactionCase):
    def setUp(self):
        super(TestController, self).setUp()
        self.Dialoglist = self.env['tspbv.dialoglist']
        self.Session = self.env['tspbv.session']
        self.Model = self.env['ir.model']
        self.workflow_1 = self.env.ref('tspbv_connector.workflow_1')
        self.dialoglist_1 = self.env.ref('tspbv_connector.dialoglist_1')
        self.dialoglist_2 = self.env.ref('tspbv_connector.dialoglist_2')
        self.dialoglist_idle = self.env.ref('tspbv_connector.dialoglist_5')
        self.dialoglist_6 = self.env.ref('tspbv_connector.dialoglist_6')
        self.session_1 = self.Session.create({
            'user_id': 1
        })

        self.stock_picking_1 = self.env.ref(
            'stock.outgoing_shipment_main_warehouse'
        )
        self.stock_picking_batch_1 = self.env.ref(
            'stock_picking_batch.stock_picking_batch_dry_1'
        )
        self.stock_move_1 = self.ref("stock_picking_batch.stock_move4")
        self.model_1 = self.Model.search([('model', '=', 'res.users')])
        self.picking_filter_1 = self.env.ref(
            'tspbv_connector.tspbv_assignment_create_picking_filter'
        )

    def test_unique_session(self):
        with self.assertRaises(IntegrityError):
            self.Session.create({
                'user_id': 1
            })

    def test_success_login(self):
        original_request = http.request
        http.request = FakeRequest(self.env)
        controller = TspbvController()
        response = controller.success(self.workflow_1.id)
        self.assertEqual(
            response.data,
            self.workflow_1.generate_init_xml(0)
        )
        http.request = original_request

    def test_dialoglist_route(self):
        original_request = http.request
        http.request = FakeRequest(self.env)
        controller = TspbvController()
        response = controller.dialoglist(self.dialoglist_1.default_code, 1)
        self.assertEqual(
            response.data,
            self.dialoglist_1.generate_dialoglist_xml(1)
        )
        http.request = original_request

    def test_dialoglist_route_complex(self):
        original_request = http.request
        http.request = FakeRequest(self.env)
        controller = TspbvController()
        response = controller.dialoglist(self.dialoglist_2.default_code, 1)
        self.assertEqual(
            response.data,
            self.dialoglist_2.generate_dialoglist_xml(1)
        )
        http.request = original_request        

    def test_dialoglist_invalid_record(self):
        original_request = http.request
        http.request = FakeRequest(self.env)
        controller = TspbvController()

        self.test_start_stock_picking_assignment()
        self.assertFalse(self.dialoglist_1.model_id)
        self.assertTrue(self.session_1.model_id)
        self.dialoglist_1.model_id = self.session_1.model_id

        with self.assertRaises(ValidationError):
            response = controller.dialoglist(self.dialoglist_1.default_code, -1)
        http.request = original_request        

    def test_start_stock_picking_assignment(self):
        original_request = http.request
        http.request = FakeRequest(self.env)
        controller = TspbvController()
        self.assertEqual(self.env.uid, 1)
        session = self.Session.search([('user_id', '=', self.env.uid)])
        self.assertEqual(session.id, self.session_1.id)
        self.assertEqual(session.model_res_id, 0)
        response = controller.start('stock.picking', self.dialoglist_1.default_code)
        self.assertEqual(session.model_res_id, self.stock_picking_1.id)
        self.assertEqual(session.user_id, self.stock_picking_1.user_id)
        http.request = original_request

    def test_start_stock_picking_batch_assignment(self):
        original_request = http.request
        http.request = FakeRequest(self.env)
        controller = TspbvController()
        self.assertEqual(self.env.uid, 1)
        session = self.Session.search([('user_id', '=', self.env.uid)])
        self.assertEqual(session.id, self.session_1.id)
        self.assertEqual(session.model_res_id, 0)
        self.assertFalse(self.session_1.current_line_ids)

        # temp check for lines
        self.assertFalse(self.session_1.current_item_id.id)
        # keep it
        response = controller.start(
            'stock.picking.batch',
            self.dialoglist_1.default_code
        )
        # temp check for lines
        self.assertEqual(self.stock_move_1, self.session_1.current_item_id.id)

        self.assertEqual(session.model_res_id, self.stock_picking_batch_1.id)
        self.assertEqual(session.user_id, self.stock_picking_batch_1.user_id)
        self.assertIn(self.stock_move_1, self.session_1.current_line_ids.ids)

        # check set of current_item
        # self.assertFalse(self.dialoglist_1.model_id)
        # self.assertTrue(self.session_1.model_id)
        # self.dialoglist_1.model_id = self.session_1.model_id
        # self.assertFalse(self.session_1.current_item_id.id)
        # response = controller.lines(self.dialoglist_6.default_code)
        # self.assertEqual(self.stock_move_1, self.session_1.current_item_id.id)
        # self.assertEqual(self.dialoglist_1.model_id, self.session_1.model_id)

        http.request = original_request

    def test_start_load_idle(self):
        original_request = http.request
        http.request = FakeRequest(self.env)
        controller = TspbvController()
        self.picking_filter_1.write({
            'domain': "[('id','<','1')]"
        })
        response = controller.start('stock.picking', 1)
        self.assertIn('dialog id="idle"', response.data)

    def test_start_load_idle_fail(self):
        original_request = http.request
        http.request = FakeRequest(self.env)
        controller = TspbvController()   
        with self.assertRaises(ValidationError):  
            self.dialoglist_idle.unlink()
            self.picking_filter_1.write({
                'domain': "[('id','<','1')]"
            })
            response = controller.start('stock.picking', 1)

    def test_start_invalid_model(self):
        original_request = http.request
        http.request = FakeRequest(self.env)
        controller = TspbvController()
        with self.assertRaises(ValidationError):
            response = controller.start('sale.order', 1)

    def test_start_without_session(self):
        original_request = http.request
        http.request = FakeRequest(self.env)
        controller = TspbvController()
        self.session_1.unlink()
        session = self.Session.search([('user_id', '=', self.env.uid)])
        self.assertFalse(session.id)
        response = controller.start(
                'stock.picking.batch',
                self.dialoglist_1.default_code
            )
        session = self.Session.search([('user_id', '=', self.env.uid)])
        self.assertEqual(session.model_res_id, self.stock_picking_batch_1.id)
        self.assertEqual(session.user_id, self.stock_picking_batch_1.user_id)
        http.request = original_request

    def test_cancel_picking_route(self):
        original_request = http.request
        http.request = FakeRequest(self.env)
        controller = TspbvController()
        self.test_start_stock_picking_assignment()
        model_rec = self.env[self.session_1.model_id.model].search([
            ('id', '=', self.session_1.model_res_id)
        ], limit=1)
        self.assertEqual(model_rec.state, 'assigned')

        response = controller.cancel(self.dialoglist_1.default_code)
        model_rec = self.env[self.session_1.model_id.model].search([
            ('id', '=', self.session_1.model_res_id)
        ], limit=1)
        self.assertEqual(model_rec.state, 'on_hold')
        model_rec.unhold()
        self.assertEqual(model_rec.state, 'assigned')
        http.request = original_request

    def test_cancel_batch_picking_route(self):
        original_request = http.request
        http.request = FakeRequest(self.env)
        controller = TspbvController()
        self.test_start_stock_picking_batch_assignment()
        model_rec = self.env[self.session_1.model_id.model].search([
            ('id', '=', self.session_1.model_res_id)
        ], limit=1)
        self.assertEqual(model_rec.state, 'in_progress')

        response = controller.cancel(self.dialoglist_1.default_code)
        model_rec = self.env[self.session_1.model_id.model].search([
            ('id', '=', self.session_1.model_res_id)
        ], limit=1)
        self.assertEqual(model_rec.state, 'on_hold')
        model_rec.unhold()
        self.assertEqual(model_rec.state, 'in_progress')
        http.request = original_request

    def test_invalid_line_model(self):
        original_request = http.request
        http.request = FakeRequest(self.env)
        controller = TspbvController()
        with self.assertRaises(ValidationError):
            controller.get_lines(
                self.session_1.model_id,
                self.session_1.model_res_id
            )
        with self.assertRaises(ValidationError):
            controller.get_lines(
                self.model_1,
                self.session_1.model_res_id
            )
