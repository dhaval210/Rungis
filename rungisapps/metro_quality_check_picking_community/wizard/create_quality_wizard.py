# -*- coding: utf-8 -*-
# 
# from odoo import api, fields, models, _
# from odoo.exceptions import UserError, Warning
# 
# class CreateQualityWizard(models.TransientModel):
#     _name = "create.quality.wizard"
# 
#     product_id = fields.Many2one(
#         'product.product',
#         string='Vehicle Condition Product',
#         required=False,
#         default=lambda self: self.env.user.company_id.vehicle_product_id.id,
#     )
#     team_id = fields.Many2one(
#         'quality.alert.team',
#         string='Team',
#         required=True,
#     )
#     starcking_product_id = fields.Many2one(
#         'product.product',
#         string='Stracking Product',
#         required=False,
#         default=lambda self: self.env.user.company_id.starcking_product_id.id,
#     )
#     door_product_id = fields.Many2one(
#         'product.product',
#         string='Vehicle Door Product',
#         required=False,
#         default=lambda self: self.env.user.company_id.door_product_id.id,
#     )
#     temprature_product_id = fields.Many2one(
#         'product.product',
#         string='Vehicle Temperature Product',
#         required=False,
#         default=lambda self: self.env.user.company_id.temprature_product_id.id,
#     )
#     product_type1 = fields.Selection(
#         [('pass','Pass'),
#          ('fail','Fail')],
#         string='Vehicle Condition Result',
#         required=False,
#     )
#     product_type2 = fields.Selection(
#         [('pass','Pass'),
#          ('fail','Fail')],
#         string='Stracking Result',
#         required=False,
#     )
#     product_type3 = fields.Selection(
#         [('pass','Pass'),
#          ('fail','Fail')],
#         string='Vehicle Door Result',
#         required=False,
#     )
#     product_type4 = fields.Selection(
#         [('pass','Pass'),
#          ('fail','Fail')],
#         string='Vehicle Temperature Result',
#         required=False,
#     )
#     custom_truck_type = fields.Selection(
#         [('chilled','Chilled'),
#          ('frozen','Frozen'),
#          ('ambient','Ambient')],
#         string='Truck Type',
#         copy=False,
#     )
#     
#     
#     @api.multi
#     def create_pass_quality(self):
#         picking_id = self.env['stock.picking'].browse(self._context.get('active_id'))
#         quality_obj = self.env['quality.check']
#         for rec in self:
#             if picking_id.custom_truck_type:
# #             if picking_id.custom_quality_id:
# #                 picking_id.custom_quality_id.write({'product_id':rec.product_id.id,
# #                                                  'team_id':rec.team_id.id})
# #                 #picking_id.custom_quality_id.do_pass()
#                 quality_vals = {'product_id':rec.product_id.id,
#                                 'team_id':rec.team_id.id,
#                                 'picking_id':picking_id.id,
#                                 'quality_state': rec.product_type1,
#                                 }
#                 quality_record = quality_obj.create(quality_vals)
#                 picking_id.custom_quality_id = quality_record.id
#                 if rec.product_type1 == 'fail':
#                     picking_id.custom_quality_id.do_fail()
#                 else:
#                     picking_id.custom_quality_id.do_pass()
#                 
#                 starcking_product_vals = {'product_id':rec.starcking_product_id.id,
#                                 'team_id':rec.team_id.id,
#                                 'picking_id':picking_id.id,
#                                 'quality_state': rec.product_type2,
#                                 }
#                 quality_record1 = quality_obj.create(starcking_product_vals)
#                 picking_id.stacking_quality_id = quality_record1.id
#                 if rec.product_type2 == 'fail':
#                     picking_id.stacking_quality_id.do_fail()
#                 else:
#                     picking_id.stacking_quality_id.do_pass()
#                 
#                 door_product_vals = {'product_id':rec.door_product_id.id,
#                                 'team_id':rec.team_id.id,
#                                 'picking_id':picking_id.id,
#                                 'quality_state': rec.product_type3,
#                                 }
#                 quality_record2 = quality_obj.create(door_product_vals)
#                 picking_id.vehicledoor_quality_id = quality_record2.id
#                 if rec.product_type3 == 'fail':
#                     picking_id.vehicledoor_quality_id.do_fail()
#                 else:
#                     picking_id.vehicledoor_quality_id.do_pass()
#                 
#                 temprature_product_vals = {'product_id':rec.temprature_product_id.id,
#                                 'team_id':rec.team_id.id,
#                                 'picking_id':picking_id.id,
#                                 'quality_state': rec.product_type4,
#                                 }
#                 quality_record3 = quality_obj.create(temprature_product_vals)
#                 picking_id.vehicle_temperature_quality_id = quality_record3.id
#                 if rec.product_type3 == 'fail':
#                     picking_id.vehicle_temperature_quality_id.do_fail()
#                 else:
#                     picking_id.vehicle_temperature_quality_id.do_pass()
#                     
#                 picking_id.custom_is_confirm_qc = True
#                 picking_id.quality_check_user_id = self.env.user.id
#                 picking_id.quality_check_date = fields.Datetime.now()
#             else:
#                 raise UserError(_('Please Select the Truck Type on Quality Checks tab.'))
#                 #quality_record.do_pass()
#             
# #     @api.multi
# #     def create_fail_quality(self):
# #         picking_id = self.env['stock.picking'].browse(self._context.get('active_id'))
# #         quality_obj = self.env['quality.check']
# #         for rec in self:
# #             if not picking_id.custom_truck_type:
# #                 raise UserError(_('Please Select the Truck Type on Quality Checks tab.'))
# #             if picking_id.custom_quality_id:
# #                 picking_id.custom_quality_id.write({'product_id':rec.product_id.id,
# #                                                  'team_id':rec.team_id.id})
# #                 picking_id.custom_quality_id.do_fail()
# #             else:
# #                 quality_vals = {'product_id':rec.product_id.id,
# #                                 'team_id':rec.team_id.id,
# #                                 'picking_id':picking_id.id,
# #                                 }
# #                 quality_record = quality_obj.create(quality_vals)
# #                 picking_id.custom_quality_id = quality_record.id
# #                 picking_id.custom_is_confirm_qc = True
# #                 picking_id.quality_check_user_id = self.env.user.id
# #                 picking_id.quality_check_date = fields.Datetime.now()
# #                 quality_record.do_fail()