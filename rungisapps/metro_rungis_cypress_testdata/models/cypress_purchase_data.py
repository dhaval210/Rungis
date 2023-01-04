from odoo import api, fields, models
import random
import string
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from random import randint

class CypressPurchaseData(models.Model):
    _name = 'cypress.purchase.data'
    _description = 'Purchase Receipt'
    _rec_name = 'name'

    name = fields.Char()
    qty = fields.Float(string="Qty")
    uom_id = fields.Many2one('uom.uom', string="UoM")
    partner_id = fields.Many2one('res.partner', string="Vendor",
                                 default=lambda self: self.env.ref("metro_rungis_cypress_testdata.cypress_partner"))

    line_ids = fields.One2many('cypress.purchase.line', 'po_id', string="Order Line")
    we_user_id = fields.Many2one('res.users', string="Wareneingang User", required=True,
                                 domain=lambda self: [('groups_id', 'in', self.env.ref('metro_security_roles.group_stock_wareneingang').id)])
    taxi_user_id = fields.Many2one('res.users', string="Taxi User", required=True)

    def get_random_string(self, length):
        letters = string.ascii_lowercase
        result_str = ''.join(random.choice(letters) for i in range(length))
        return result_str

    def get_package(self):
        result_str = ''.join(["{}".format(randint(0, 9)) for num in range(0, 4)])
        return "$RE" + result_str


    def action_create_purchase_order(self):
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner_id.id,
             })
        vals = []
        for line in self.line_ids:
            vals.append((0, 0, {
                'product_id': line.product_id.id,
                'name': line.name,
                'product_uom': line.uom_id,
                'product_qty': line.qty if line.qty >= 1 else 1,
                'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'price_unit': line.price_unit if line.price_unit >= 1 else 100
            }))
        purchase_order.order_line = vals
        purchase_order.order_line = vals
        purchase_order.sudo().button_confirm()
        picking_ids = purchase_order.picking_ids
        gate_id = self.env.ref('metro_rungis_cypress_testdata.cypress_stock_gate')
        if self.env.ref('metro_rungis_cypress_testdata.cypress_stock_gate').state == True:
            gate_string = self.get_random_string(2)
            gate_id = self.env['stock.gate'].create({
                'name': "Test Tor%s" %gate_string
            })
        picking_ids.write({
            'gate_id': gate_id.id
        })
        for line in picking_ids.move_line_ids_without_package:
            flag = 1

            while flag != 0:
                package_name = self.get_package()
                package_id = self.env['stock.quant.package'].sudo(self.we_user_id.id).create({
                    'name': package_name,
                })
                pack = str(random.randint(10, 99)) + self.get_random_string(6)
                check_lot_exist = self.env['stock.production.lot'].search([('name', '=', pack)])
                if not check_lot_exist:
                    flag = 0
                    lot = self.env['stock.production.lot'].sudo(self.we_user_id.id).create({
                        'name': pack,
                        'product_id': line.product_id.id,
                        'product_qty': line.product_uom_qty,
                    })
                    line.write({
                        'lot_id': lot.id,
                        'lot_name': lot.name,
                        'package_id': package_id.id
                    })
                else:
                    flag = 1
        wiz = picking_ids.sudo(self.we_user_id.id).button_validate()
        wizard_id = self.env[wiz['res_model']].browse(wiz['res_id'])
        wizard_id.sudo(self.we_user_id.id).process()
        picking_list = self.env['stock.picking'].search([('origin', '=', purchase_order.name),
                                                         ('state', '=', 'assigned')])
        for picking in picking_list:
            product_id = picking.move_line_ids_without_package.mapped('product_id')
            cypress_line_id = self.line_ids.filtered(lambda l: l.product_id == product_id)
            picking.write({
                'location_dest_id': cypress_line_id.location_dest_id.id
            })
            move_line_ids = picking.move_line_ids_without_package
            product_id = picking.move_line_ids_without_package.mapped('product_id')
            for line in move_line_ids:
                product_id = picking.move_line_ids_without_package.mapped('product_id')
                cypress_line_id = self.line_ids.filtered(lambda l: l.product_id == product_id)
                line.write({
                'location_dest_id': cypress_line_id.location_dest_id.id
                })
            picking_wiz = picking.sudo(self.taxi_user_id.id).button_validate()
            picki_wizard_id = self.env[picking_wiz['res_model']].browse(picking_wiz['res_id'])
            picki_wizard_id.sudo(self.taxi_user_id.id).process()

    @api.onchange('we_user_id')
    def _onchange_we_user_id(self):
        role_id = self.env.ref('metro_security_roles.role_wareneingang')
        return {'domain': {'we_user_id': [('id', 'in', role_id.line_ids.mapped('user_id').ids)]}}

    @api.onchange('taxi_user_id')
    def _onchange_taxi_user_id(self):
        role_id = self.env.ref('metro_security_roles.role_taxi')
        return {'domain': {'taxi_user_id': [('id', 'in', role_id.line_ids.mapped('user_id').ids)]}}


class CypressPurchaseLine(models.Model):
    _name = 'cypress.purchase.line'
    _description = "Cypress Purchase Order Line"

    product_id = fields.Many2one('product.product', string="Product", required=True, domain="[('catch_weight_ok','=', False)]")
    name = fields.Char(string="Name", required=True)
    qty = fields.Float(string="Quantity", required=True)
    price_unit = fields.Float(string="Price", required=True)
    uom_id = fields.Many2one('uom.uom', string="UoM", required=True)
    po_id = fields.Many2one('cypress.purchase.data')
    location_dest_id = fields.Many2one('stock.location', string="Destination Location",
                                       domain="[('usage', '=', 'internal')]", required=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.uom_id = False
        self.name = self.product_id.display_name
        self.uom_id = self.product_id.uom_id.id
        self.qty = 1
        self.price_unit = self.product_id.standard_price if self.product_id.standard_price > 0 else 1

