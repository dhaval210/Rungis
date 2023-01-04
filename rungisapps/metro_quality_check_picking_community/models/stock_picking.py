# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning

class Picking(models.Model):
    _inherit = "stock.picking"

    # def init(self, force=False):
    #     pickings = self.with_context(prefetch_fields=False).search([('is_skip_quality_check', '=', False)])
    #     pickings.compute_skip_quality_check()
    #
    custom_truck_type = fields.Selection(
        [('chilled','Chilled'),
         ('frozen','Frozen'),
         ('ambient','Ambient'),
         ('chilled_frozen','Chilled and Frozen')],
        string='Truck Type',
        copy=False,
    )
    custom_vehicle_condition = fields.Boolean(
        string='Vehicle condition & personal Hygiene of the person accompanying the Vehicle',
        help='Vehicle condition & personal Hygiene of the person accompanying the Vehicle - Acceptable/Not Acceptable',
        copy=False,
    )
    custom_stacking_arragment = fields.Boolean(
        string='Stacking & Arrangement of Products in the vehicle during receipt',
        help='Stacking & Arrangement of Products in the vehicle during receipt – Proper/Improper',
        copy=False,
    )
    custom_vehicle_door = fields.Boolean(
        string='Vehicle Door Sealed',
        help='Vehicle door sealed Yes/No',
        copy=False,
    )
    custom_vehicle_temprature = fields.Float(
        string='Vehicle Frozen Temperature',
        help='Vehicle temperature : Measured Temperature in Deg.C - user need to enter the temperature \
             *(Applicable on Chilled and Frozen Truck)* \
             1. Chilled Truck Acceptable Temperature → 0 - 4°C \
             2. Frozen Truck Acceptable Temperature → -18°C ± 2°C',
        copy=False,
    )
    custom_chilled_temperature = fields.Float(
        string='Vehicle Chilled Temperature',
        copy=False,
    )
    custom_is_confirm_qc = fields.Boolean(
        string='Is Confirm QC?',
        readonly=True,
        copy=False,
    )
    is_skip_quality_check = fields.Boolean(
        string='Is Skip Quality Check?',
        copy=False,
        compute='compute_skip_quality_check',
        store=True,
    )
    custom_internal_notes = fields.Text(
        string='Internal Notes',
        copy=False,
    )
    quality_check_user_id = fields.Many2one(
        'res.users',
        string='Quality Check User',
        copy=False,
        readonly=True,
    )
    quality_check_date = fields.Datetime(
        string='Quality Check Date',
        readonly=True,
        copy=False,
    )
    custom_quality_id = fields.Many2one(
        'quality.inspection',
        string='Vehicle Condition Quality',
        readonly=True,
        copy=False,
    )
    stacking_quality_id = fields.Many2one(
        'quality.inspection',
        string='Stacking Condition Quality',
        readonly=True,
        copy=False,
    )
    vehicledoor_quality_id = fields.Many2one(
        'quality.inspection',
        string='Vehicle Door Quality',
        readonly=True,
        copy=False,
    )
    vehicle_temperature_quality_id = fields.Many2one(
        'quality.inspection',
        string='Vehicle Frozen Temperature Quality',
        readonly=True,
        copy=False,
    )
    vehicle_chilled_temperature_quality_id = fields.Many2one(
        'quality.inspection',
        string='Vehicle Chilled Temperature Quality',
        readonly=True,
        copy=False,
    )
    custom_quality_state = fields.Selection(
        related='custom_quality_id.state',
        string='Vehicle Condition Quality State',
        readonly=True,
        copy=False,
    )
    custom_stacking_quality_state = fields.Selection(
        related='stacking_quality_id.state',
        string='Stacking Quality State',
        readonly=True,
        copy=False,
    )
    custom_vehicledoor_quality_state = fields.Selection(
        related='vehicledoor_quality_id.state',
        string='Vehicle Door Quality State',
        readonly=True,
        copy=False,
    )
    custom_temperature_quality_state = fields.Selection(
        related='vehicle_temperature_quality_id.state',
        string='Vehicle Frozen Temperature Quality State',
        readonly=True,
        copy=False,
    )
    custom_chilled_temperature_quality_state = fields.Selection(
        related='vehicle_chilled_temperature_quality_id.state',
        string='Vehicle Chilled Temperature Quality State',
        readonly=True,
        copy=False,
    )
    # custom_quality_team_id = fields.Many2one(
    #     'quality.control.alert.team',
    #     default=lambda self: self._get_custom_quality_team_id(),#lambda self: self.env.user.company_id.custom_quality_team_id,
    #     string='Quality Team',
    #     copy=False,
    # )
    purchase_state = fields.Selection(
        related="purchase_id.state",
        store=True,
        string='Purchase State',
    )


    @api.depends('picking_type_id','picking_type_id.code', 'move_lines')
    def compute_skip_quality_check(self):
        for rec in self:
            for line in rec.move_lines:
                if line.purchase_line_id:
                    rec.is_skip_quality_check = True if rec.picking_type_id.code == 'incoming' \
                                                        and not rec.location_id.usage == 'customer' else False


    @api.multi
    def button_validate(self):
        self.ensure_one()
        if self.is_skip_quality_check and not self.custom_is_confirm_qc:
#                 if pick.custom_quality_state != 'pass' or pick.custom_stacking_quality_state != 'pass' or pick.custom_vehicledoor_quality_state != 'pass' or pick.custom_temperature_quality_state != 'pass':
#                     raise UserError(_('You are not allowed to transfer the stock without completing the quality check!'))
            raise UserError(_('You are not allowed to transfer the stock without completing the quality check!'))
        return super(Picking, self).button_validate()


#     @api.multi
#     @api.constrains('custom_vehicle_temprature')
#     def check_custom_vehicle_temprature(self):
#         for rec in self:
#             if rec.custom_truck_type == 'chilled':
#                 if rec.custom_vehicle_temprature < 0 or rec.custom_vehicle_temprature > 4:
#                     raise Warning('Chilled Truck Acceptable Temperature Between → 0 - 4°C.')
#             if rec.custom_truck_type == 'frozen':
#                 if rec.custom_vehicle_temprature < -18 or rec.custom_vehicle_temprature > +2:
#                     raise Warning('Frozen Truck Acceptable Temperature between → -18°C ± 2°C.')

    @api.model
    def _get_vehicle_product_id(self):
        vehicle_product_id = self.env['ir.default'].get('res.config.settings', 'vehicle_product_id')
        if not vehicle_product_id:
            raise UserError(_(
                'You Forgot To Configure Quality Check Products In Inventory '
                'Settings'))
        return vehicle_product_id

    @api.model
    def _get_door_product_id(self):
        door_product_id = self.env['ir.default'].get('res.config.settings', 'door_product_id')
        return door_product_id

    @api.model
    def _get_stracking_product_id(self):
        stracking_product_id = self.env['ir.default'].get('res.config.settings', 'stracking_product_id')
        return stracking_product_id

    @api.model
    def _get_temprature_product_id(self):
        temprature_product_id = self.env['ir.default'].get('res.config.settings', 'temprature_product_id')
        return temprature_product_id

    @api.model
    def _get_chilled_temprature_product_id(self):
        chilled_temprature_product_id = self.env['ir.default'].get('res.config.settings', 'chilled_temprature_product_id')
        return chilled_temprature_product_id

    # @api.model
    # def _get_custom_quality_team_id(self):
    #     custom_quality_team_id = self.env['ir.default'].get(
    #         'res.config.settings', 'custom_quality_team_id')
    #     return custom_quality_team_id

    @api.multi
    def create_quality_check(self):
        team_id =self.env['ir.default'].get(
            'res.config.settings', 'custom_quality_team_id')
        for rec in self:
            vehicle_product_id = self._get_vehicle_product_id()
            door_product_id = self._get_door_product_id()
            stracking_product_id = self._get_stracking_product_id()
            temprature_product_id = self._get_temprature_product_id()
            chilled_temprature_product_id = self._get_chilled_temprature_product_id()

            quality_obj = self.env['quality.inspection']
            if not rec.custom_truck_type:
                raise UserError(_('Please Select the Truck Type on Quality Checks tab.'))
            if rec.custom_truck_type == 'chilled' or rec.custom_truck_type == 'frozen':


                vehicle_product_id = self._get_vehicle_product_id()
                door_product_id = self._get_door_product_id()
                stracking_product_id = self._get_stracking_product_id()
                temprature_product_id = self._get_temprature_product_id()
                chilled_temprature_product_id = self._get_chilled_temprature_product_id()

                #For Vehicle Condition Product
                quality_vals = {
                                'product_id': vehicle_product_id,#rec.company_id.vehicle_product_id.id,
                                'team_id': team_id,
                                'picking_id':rec.id,
                                'custom_product_type': 'vehicle_condition',
                                }
                quality_record = quality_obj.create(quality_vals)
                rec.custom_quality_id = quality_record.id

                if rec.custom_vehicle_condition != True:
                    rec.custom_quality_id.do_fail()
                else:
                    rec.custom_quality_id.do_pass()

                #For Vehicle Door Product
#                 vehicle_door_quality_vals = {
#                                 'product_id': door_product_id,#rec.company_id.door_product_id.id,
#                                 'team_id':rec.custom_quality_team_id.id,
#                                 'picking_id':rec.id,
#                                 'custom_product_type': 'vehicle_door',
#                                 }
#                 vehicle_door_quality_record = quality_obj.create(vehicle_door_quality_vals)
#                 rec.vehicledoor_quality_id = vehicle_door_quality_record.id
#
#                 if rec.custom_vehicle_door != True:
#                     rec.vehicledoor_quality_id.do_fail()
#                 else:
#                     rec.vehicledoor_quality_id.do_pass()
#
                #For Stacking Arragment Product
                stacking_quality_vals = {
                                'product_id': stracking_product_id,#rec.company_id.starcking_product_id.id,
                                'team_id':team_id,
                                'picking_id':rec.id,
                                'custom_product_type': 'stacking_arrangement',
                                }
                stacking_quality_record = quality_obj.create(stacking_quality_vals)
                rec.stacking_quality_id = stacking_quality_record.id

                if rec.custom_stacking_arragment != True:
                    rec.stacking_quality_id.do_fail()
                else:
                    rec.stacking_quality_id.do_pass()

                #for Temprature Product
                if rec.custom_truck_type == 'chilled':
                        vehicle_temprature_quality_vals = {
                            'product_id': chilled_temprature_product_id,#rec.company_id.temprature_product_id.id,
                            'team_id':team_id,
                            'picking_id':rec.id,
                            'custom_product_type': 'vehicle_temprature',
                        }
                        vehicle_temprature_quality_record = quality_obj.create(vehicle_temprature_quality_vals)
                        rec.vehicle_chilled_temperature_quality_id = vehicle_temprature_quality_record.id

#                        if rec.custom_chilled_temperature < 0 or rec.custom_chilled_temperature > 4:
                        # Date: 2 Feb 2018 Chilled Temprature Range 0 to 4 change with 0 to 6
                        if rec.custom_chilled_temperature >= 0.0 and rec.custom_chilled_temperature <= 6.0:#range(round(0), round(4)):
                            rec.vehicle_chilled_temperature_quality_id.do_pass()
                        else:
                            rec.vehicle_chilled_temperature_quality_id.do_fail()
#                             rec.stacking_quality_id.do_pass()

                if rec.custom_truck_type == 'frozen':
                    vehicle_temprature_quality_vals = {
                                        'product_id': temprature_product_id,#rec.company_id.temprature_product_id.id,
                                        'team_id':team_id,
                                        'picking_id':rec.id,
                                        'custom_product_type': 'vehicle_temprature',
                                        }
                    vehicle_temprature_quality_record = quality_obj.create(vehicle_temprature_quality_vals)
                    rec.vehicle_temperature_quality_id = vehicle_temprature_quality_record.id

                    #if rec.custom_vehicle_temprature >= -16 or rec.custom_vehicle_temprature <= -30:
                    if rec.custom_vehicle_temprature <= -16.0 and rec.custom_vehicle_temprature >= -30.0:
                        rec.vehicle_temperature_quality_id.do_pass()
                    else:
                        rec.vehicle_temperature_quality_id.do_fail()

                rec.custom_is_confirm_qc = True
                rec.quality_check_user_id = self.env.user.id
                rec.quality_check_date = fields.Datetime.now()

            if rec.custom_truck_type == 'chilled_frozen':
                vehicle_product_id = self._get_vehicle_product_id()
                door_product_id = self._get_door_product_id()
                stracking_product_id = self._get_stracking_product_id()
                temprature_product_id = self._get_temprature_product_id()
                chilled_temprature_product_id = self._get_chilled_temprature_product_id()

                #For Vehicle Condition Product
                quality_vals = {
                                'product_id': vehicle_product_id,#rec.company_id.vehicle_product_id.id,
                                'team_id': team_id,
                                'picking_id':rec.id,
                                'custom_product_type': 'vehicle_condition',
                                }
                quality_record = quality_obj.create(quality_vals)
                rec.custom_quality_id = quality_record.id

                if rec.custom_vehicle_condition != True:
                    rec.custom_quality_id.do_fail()
                else:
                    rec.custom_quality_id.do_pass()

                #For Vehicle Door Product
#                 vehicle_door_quality_vals = {
#                                 'product_id': door_product_id,#rec.company_id.door_product_id.id,
#                                 'team_id':rec.custom_quality_team_id.id,
#                                 'picking_id':rec.id,
#                                 'custom_product_type': 'vehicle_door',
#                                 }
#                 vehicle_door_quality_record = quality_obj.create(vehicle_door_quality_vals)
#                 rec.vehicledoor_quality_id = vehicle_door_quality_record.id
#
#                 if rec.custom_vehicle_door != True:
#                     rec.vehicledoor_quality_id.do_fail()
#                 else:
#                     rec.vehicledoor_quality_id.do_pass()

                #For Stacking Arragment Product
                stacking_quality_vals = {
                                'product_id': stracking_product_id,#rec.company_id.starcking_product_id.id,
                                'team_id':team_id,
                                'picking_id':rec.id,
                                'custom_product_type': 'stacking_arrangement',
                                }
                stacking_quality_record = quality_obj.create(stacking_quality_vals)
                rec.stacking_quality_id = stacking_quality_record.id

                if rec.custom_stacking_arragment != True:
                    rec.stacking_quality_id.do_fail()
                else:
                    rec.stacking_quality_id.do_pass()


                vehicle_temprature_quality_vals = {
                    'product_id': temprature_product_id,#rec.company_id.temprature_product_id.id,
                    'team_id':team_id,
                    'picking_id':rec.id,
                    'custom_product_type': 'vehicle_temprature',
                }
                vehicle_temprature_quality_record = quality_obj.create(vehicle_temprature_quality_vals)
                rec.vehicle_temperature_quality_id = vehicle_temprature_quality_record.id

                #if rec.custom_vehicle_temprature < 0 or rec.custom_vehicle_temprature > 4:
                #if rec.custom_vehicle_temprature in range(-30, -16):
                if rec.custom_vehicle_temprature <= -16.0 and rec.custom_vehicle_temprature >= -30.0:
                    rec.vehicle_temperature_quality_id.do_pass()
                else:
                    rec.vehicle_temperature_quality_id.do_fail()

                vehicle_temprature_quality_vals = {
                    'product_id': chilled_temprature_product_id,#rec.company_id.temprature_product_id.id,
                    'team_id':team_id,
                    'picking_id':rec.id,
                    'custom_product_type': 'vehicle_temprature',
                }
                vehicle_temprature_quality_record = quality_obj.create(vehicle_temprature_quality_vals)
                rec.vehicle_chilled_temperature_quality_id = vehicle_temprature_quality_record.id

                #if rec.custom_vehicle_temprature >= -16 or rec.custom_vehicle_temprature <= -30:
#                 if rec.custom_chilled_temperature in range(0, 4):
                #  Date: 2 Feb 2018 Chilled Temprature Range 0 to 4 change with 0 to 6
                if rec.custom_chilled_temperature >= 0.0 and rec.custom_chilled_temperature <= 6.0:
                    rec.vehicle_chilled_temperature_quality_id.do_pass()
                else:
                    rec.vehicle_chilled_temperature_quality_id.do_fail()

                rec.custom_is_confirm_qc = True
                rec.quality_check_user_id = self.env.user.id
                rec.quality_check_date = fields.Datetime.now()


            if rec.custom_truck_type == 'ambient':
#                 if rec.custom_vehicle_condition != True or rec.custom_vehicle_door != True or rec.custom_stacking_arragment != True:
#                     raise UserError(_('You are not allowed to transfer the stock without completing the quality check!'))
#                 else:
                quality_obj = self.env['quality.inspection']
                #if rec.custom_vehicle_condition != True or rec.custom_vehicle_door != True or rec.custom_stacking_arragment != True:
                quality_vals = {
                            'product_id': vehicle_product_id,#rec.company_id.vehicle_product_id.id,
                            'team_id':team_id,
                            'picking_id':rec.id,
                            'custom_product_type': 'vehicle_condition',
                            }
                quality_record = quality_obj.create(quality_vals)
                rec.custom_quality_id = quality_record.id

                if rec.custom_vehicle_condition != True:
                    rec.custom_quality_id.do_fail()
                else:
                    rec.custom_quality_id.do_pass()

                stacking_quality_vals = {
                            'product_id': stracking_product_id, #starcking_product_id,#rec.company_id.starcking_product_id.id,
                            'team_id':team_id,
                            'picking_id':rec.id,
                            'custom_product_type': 'stacking_arrangement',
                            }
                stacking_quality_record = quality_obj.create(stacking_quality_vals)
                rec.stacking_quality_id = stacking_quality_record.id

                if rec.custom_stacking_arragment != True:
                    rec.stacking_quality_id.do_fail()
                else:
                    rec.stacking_quality_id.do_pass()

#                 vehicle_door_quality_vals = {
#                             'product_id': door_product_id,#rec.company_id.door_product_id.id,
#                             'team_id':rec.custom_quality_team_id.id,
#                             'picking_id':rec.id,
#                             'custom_product_type': 'vehicle_door',
#                             }
#                 vehicle_door_quality_record = quality_obj.create(vehicle_door_quality_vals)
#                 rec.vehicledoor_quality_id = vehicle_door_quality_record.id

#                 if rec.custom_vehicle_door != True:
#                     rec.vehicledoor_quality_id.do_fail()
#                 else:
#                     rec.vehicledoor_quality_id.do_pass()

                rec.custom_is_confirm_qc = True
                rec.quality_check_user_id = self.env.user.id
                rec.quality_check_date = fields.Datetime.now()

