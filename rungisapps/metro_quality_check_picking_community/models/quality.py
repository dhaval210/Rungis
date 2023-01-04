# -*- coding: utf-8 -*-

from odoo import api, fields, models

class QualityCheck(models.Model):
    _inherit = "quality.inspection"

    custom_truck_type = fields.Selection(
        [('chilled','Chilled'),
         ('frozen','Frozen'),
         ('ambient','Ambient')],
        string='Truck Type',
        related='picking_id.custom_truck_type',
        copy=False,
    )
    custom_vehicle_condition = fields.Boolean(
        string='Vehicle condition & personal Hygiene of the person accompanying the Vehicle',
        help='Vehicle condition & personal Hygiene of the person accompanying the Vehicle',
        related='picking_id.custom_vehicle_condition',
        copy=False,
        
    )
    custom_stacking_arragment = fields.Boolean(
        string='Stacking & Arrangement of Products in the vehicle during receipt',
        help='Stacking & Arrangement of Products in the vehicle during receipt',
        related='picking_id.custom_stacking_arragment',
        copy=False,
    )
    custom_vehicle_door = fields.Boolean(
        string='Vehicle Door Sealed',
        related='picking_id.custom_vehicle_door',
        copy=False,
    )
    custom_vehicle_temprature = fields.Float(
        string='Frozen Temperature',
        related='picking_id.custom_vehicle_temprature',
        copy=False,
    )
    custom_chilled_temprature = fields.Float(
        string='Chilled Temperature',
        related='picking_id.custom_chilled_temperature',
        copy=False,
    )
    quality_check_user_id = fields.Many2one(
        'res.users',
        related='picking_id.quality_check_user_id',
        string='Quality Check User',
        copy=False,
        readonly=True,
    )
    quality_check_date = fields.Datetime(
        string='Quality Check Date',
        related='picking_id.quality_check_date',
        readonly=True,
        copy=False,
    )
    custom_internal_notes = fields.Text(
        string='Internal Notes',
        related='picking_id.custom_internal_notes',
        readonly=True,
        copy=False,
    )
    custom_product_type = fields.Selection(
        [('vehicle_condition','Vehicle Condition'),
         ('stacking_arrangement','Stacking & Arrangement'),
         ('vehicle_door','Vehicle Door'),
         ('vehicle_temprature','Vehicle Temprature'),
         ],
        string="Product Type"
    )