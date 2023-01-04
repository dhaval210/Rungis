# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    @api.depends('picking_transport_ids')
    def _picking_transport_count(self):
        for rec in self:
            rec.picking_transport_count = len(rec.picking_transport_ids)

    transporter_id = fields.Many2one(
        'res.partner',
        string="Transporter",
    )
    lr_number = fields.Char(
        string="LR Number",
        copy=True,
        required=False,
    )
    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string="Vehicle",
    )
    vehicle_driver = fields.Many2one(
        'res.partner',
        string="Vehicle Driver",
        related='vehicle_id.driver_id',
    )
    no_of_parcel = fields.Float(
        string="No of Parcels",
        copy=True,
        required=False,
    )
    picking_transport_ids = fields.One2many(
        'picking.transport.info',
        'delivery_id',
        string="Picking Transport",
    )
    picking_transport_count = fields.Integer(
        compute = '_picking_transport_count',
        store=True,
     )
    picking_route_ids = fields.One2many(
        'picking.route',
        'delivery_id',
        string='Picking Route',
    )
    transporter_route_id = fields.Many2one(
        'transporter.route',
        string='Transport Route',
    )
    transport_date = fields.Datetime(
        string='Transport Date',
        default=fields.Date.today(),
    )

    @api.multi
    def _write(self,vals):
        for rec in self:
            if vals.get('sale_id',False):
                sale = self.env['sale.order'].browse(vals['sale_id'])
                vals.update({'transporter_id' : sale.transporter_id.id})
        return super(StockPicking, self)._write(vals)

    @api.multi
    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        picking_transport_info = self.env['picking.transport.info']
        for rec in self:
            if rec.transporter_id:
                vals = {
                    'saleorder_id': rec.sale_id.id,
                    'lr_number' : rec.lr_number,
                    'transporter_id': rec.transporter_id.id,
                    'vehicle_id' : rec.vehicle_id.id,
                    'vehicle_driver' : rec.vehicle_driver.id,
                    'transport_date' : fields.Date.today(),
                    'delivery_id' : rec.id,
                    'customer_id' : rec.partner_id.id,
                    'destination_id' : rec.location_dest_id.id,
                    'carrier_id' : rec.carrier_id.id,
                    'carrier_tracking_ref' : rec.carrier_tracking_ref,
                    'weight' : rec.weight,
                    'shipping_weight' : rec.shipping_weight,
                    'number_of_packages' : rec.number_of_packages,
                    'weight_uom_id' : rec.weight_uom_id.id,
                    'no_of_parcel' :rec.no_of_parcel,
                    'user_id' : self.env.user.id,
                    'transport_date' : rec.transport_date,
                }
                info_create = picking_transport_info.create(vals)
                for line in rec.picking_route_ids:
                    line.delivery_route_id = info_create.id
        return res

    @api.multi
    def show_picking_transport(self):
        for rec in self:
            res = self.env.ref('odoo_transport_management.action_picking_transport_info')
            res = res.read()[0]
            res['domain'] = str([('id','in',rec.picking_transport_ids.ids)])
        return res

    @api.multi
    def compute_transporter_route(self):
        self.picking_route_ids.unlink()
        for rec in self:
            #for line in rec.transporter_route_id:
            for val in rec.transporter_route_id.route_line_ids:
                picking_route_vals = {
                    'source_location': val.source_location.id,
                    'destination_location' : val.destination_location.id,
                    'distance' : val.distance,
                    'hour' : val.hour,
                    'delivery_id' : rec.id,
                }
                picking_route = self.env['picking.route'].create(picking_route_vals)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
