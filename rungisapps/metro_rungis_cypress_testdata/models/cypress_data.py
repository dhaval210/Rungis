from odoo import api, fields, models
import random
import string


class CypressData(models.Model):
    _name = 'cypress.data'
    _description = 'Set Qty for Cypress Tests'

    name = fields.Char()
    product_id = fields.Many2one(comodel_name='product.product')
    partner_id = fields.Many2one('res.partner', domain=[('supplier', '=', True)])

    def get_random_string(self, length):
        letters = string.ascii_lowercase
        result_str = ''.join(random.choice(letters) for i in range(length))
        return result_str

    def create_quant(self, product, location, qty):
        pack = self.get_random_string(12)
        package = self.env['stock.quant.package'].create({
            'name': pack,
        })
        lot = self.env['stock.production.lot'].create({
            'name': pack,
            'product_id': product.id,
            'product_qty': qty,
            'cw_product_qty': product.average_cw_quantity * qty
        })
        self.env['stock.quant'].create({
            'location_id': location,
            'product_id': product.id,
            'quantity': qty,
            'reserved_quantity': 0,
            'cw_stock_quantity': product.average_cw_quantity * qty,
            'cw_stock_reserved_quantity': 0,
            'catch_weight_ok': product.catch_weight_ok,
            'product_uom_id': product.uom_id.id,
            'product_cw_uom': product.cw_uom_id.id,
            'package_id': package.id,
            'lot_id': lot.id,
        })

    def reset_product_data(self):
        loc_1 = self.env.ref('metro_rungis_cypress_testdata.cypress_location_1').id
        loc_2 = self.env.ref('metro_rungis_cypress_testdata.cypress_location_2').id
        quants = self.env['stock.quant'].search([
            ("location_id", "in", [loc_1, loc_2]),
            ("product_id", "=", self.product_id.id)
        ])
        move_line_ids = []
        warning = ''
        for quant in quants:
            move_lines = self.env["stock.move.line"].search([
                ('product_id', '=', quant.product_id.id),
                ('location_id', '=', quant.location_id.id),
                ('lot_id', '=', quant.lot_id.id),
                ('package_id', '=', quant.package_id.id),
                ('owner_id', '=', quant.owner_id.id),
            ])
            try:
                move_lines.with_context(bypass_reservation_update=True).write({
                    'product_uom_qty': 0,
                    'product_cw_uom_qty': 0
                })
                quant.write({
                    'reserved_quantity': 0,
                    'quantity': 0,
                    'cw_stock_quantity': 0,
                    'cw_stock_reserved_quantity': 0
                })
            except Exception as identifier:
                print(identifier)

        pickings = self.env['stock.picking'].search([
            ('state', 'in', ['assigned', 'waiting', 'confirmed']),
            ('picking_type_id', '=', 10),
        ])

        # for pick in pickings:
        for picking in pickings:
            for move in picking.move_lines:
                if move.reserved_availability == 0:
                    picking.do_unreserve()
                    picking.action_cancel()
                    break

    def action_set_qty_one_location(self):
        loc_1 = self.env.ref('metro_rungis_cypress_testdata.cypress_location_1').id
        self.reset_product_data()
        self.create_quant(self.product_id, loc_1, 999)

        return True

    def action_set_qty_two_locations(self):
        loc_2 = self.env.ref('metro_rungis_cypress_testdata.cypress_location_2').id
        self.action_set_qty_one_location()
        self.create_quant(self.product_id, loc_2, 15)
        return True
