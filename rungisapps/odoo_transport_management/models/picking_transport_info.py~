# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class PickingTransportInfo(models.Model):
    _name = 'picking.transport.info'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order= 'id desc'

    name = fields.Char(
        string='Number',
        readonly=True,
    )
    state = fields.Selection([
        ('draft', 'Start'),
        ('halt', 'Halt'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ('res', 'Rescheduled'),
        ],
        default='draft',
        track_visibility='onchange',
        copy=False,
    )
    saleorder_id = fields.Many2one(
        'sale.order',
        string="Sale Order",
    )
    transporter_id = fields.Many2one(
        'res.partner',
        string="Transporter",
        #related='delivery_id.transporter_id',
        required=True,
        #store=True,
    )
    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string="Vehicle",
    )
    vehicle_driver = fields.Many2one(
        'res.partner',
        string="Vehicle Driver",
        #related='vehicle_id.driver_id',
    )
    transport_date = fields.Datetime(
        string='Transport Date',
        required=True,
        default=fields.Date.today(),
    )
    delivery_id = fields.Many2one(
        'stock.picking',
        string='Picking',
    )
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
    )
    destination_id = fields.Many2one(
        'stock.location',
        string='Destination Location',
    )
    lr_number = fields.Char(
        string="LR Number",
        #related='delivery_id.lr_number',
        store=True,
    )
    carrier_id = fields.Many2one(
        'delivery.carrier',
        string='Carrier',
        #related='delivery_id.carrier_id',
    )
    carrier_tracking_ref = fields.Char(
        string='Tracking Reference',
        #related='delivery_id.carrier_tracking_ref',
    )
    weight = fields.Float(
        string='Weight',
        #related='delivery_id.weight',
    )
    shipping_weight = fields.Float(
        string='Weight for Shipping',
        #related='delivery_id.shipping_weight',
    )
    number_of_packages = fields.Integer(
        string='Number of Packages',
        #related='delivery_id.number_of_packages',
    )
    weight_uom_id = fields.Many2one(
        'product.uom',
        string='Weight Um',
        #related='delivery_id.weight_uom_id',
    )
    no_of_parcel = fields.Float(
        string="No of Parcels",
        #related='delivery_id.no_of_parcel',
    )
    picking_route_ids = fields.One2many(
        'picking.route',
        'delivery_route_id',
        string='Picking Route',
        copy=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string='Responsible User',
        default=lambda self: self.env.user.id, 
    )
    company_id = fields.Many2one(
        'res.company', 
        default=lambda self: self.env.user.company_id, 
        string='Company',
        readonly=True,
    )
    note = fields.Text(
        string='Notes',
    )

    @api.multi
    def picking_hold(self):
        for rec in self:
            rec.state = 'halt'

    @api.multi
    def picking_done(self):
        for rec in self:
            rec.state = 'done'

    @api.multi
    def picking_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    @api.multi
    def picking_reschedule(self):
        for rec in self:
            reschedule = rec.copy()
            rec.write({'picking_transport_info_id' : reschedule.id})
            res = self.env.ref('odoo_transport_management.action_picking_transport_info')
            res = res.read()[0]
            res['domain'] = str([('id','=', reschedule.id)])
            rec.state = 'res'
        return res

    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].next_by_code('picking.transport.seq')
        vals.update({
        'name': name
        })
        return super(PickingTransportInfo, self).create(vals)

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'cancel':
                raise UserError(_('You can not delete record in this state.'))
        return super(PickingTransportInfo, self).unlink()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
