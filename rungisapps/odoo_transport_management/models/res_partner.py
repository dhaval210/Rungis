# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Partner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    @api.depends('vehicle_ids')
    def _vehicle_count(self):
        for rec in self:
            rec.vehicle_count  = len(rec.vehicle_ids)

    vehicle_count = fields.Integer(
        string='Vehicles',
        store=True,
        compute = '_vehicle_count',
     )
    vehicle_ids = fields.One2many(
        'fleet.vehicle',
        'transporter_id',
        string='Vehicles',
    )

    @api.multi
    def show_vehicle(self):
        for rec in self:
            res = self.env.ref('fleet.fleet_vehicle_action')
            res = res.read()[0]
            res['domain'] = str([('id','in',rec.vehicle_ids.ids)])
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
