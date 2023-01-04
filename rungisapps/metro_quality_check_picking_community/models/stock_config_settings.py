# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    vehicle_product_id = fields.Many2one(
        'product.product',
        string='Vehicle Condition Product',
    )
    stracking_product_id = fields.Many2one(
        'product.product',
        string='Stacking Product',
    )
    door_product_id = fields.Many2one(
        'product.product',
        string='Vehicle Door Product',
    )
    temprature_product_id = fields.Many2one(
        'product.product',
        string='Frozen Temperature Product',
    )
    chilled_temprature_product_id = fields.Many2one(
        'product.product',
        string='Chilled Temperature Product',
    )
    custom_quality_team_id = fields.Many2one(
        'quality.control.alert.team',
        string='Quality Team',
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ir_default = self.env['ir.default'].sudo()
        res_values = {
            'vehicle_product_id': ir_default.get('res.config.settings', 'vehicle_product_id'),
            'stracking_product_id': ir_default.get('res.config.settings', 'stracking_product_id'),
            'door_product_id': ir_default.get('res.config.settings', 'door_product_id'),
            'temprature_product_id': ir_default.get('res.config.settings', 'temprature_product_id'),
            'chilled_temprature_product_id': ir_default.get('res.config.settings', 'chilled_temprature_product_id'),
            'custom_quality_team_id': ir_default.get('res.config.settings', 'custom_quality_team_id')
            }
        res.update(res_values)
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ir_default = self.env['ir.default'].sudo()
        ir_default.set('res.config.settings', 'vehicle_product_id', self.vehicle_product_id.id)
        ir_default.set('res.config.settings', 'stracking_product_id', self.stracking_product_id.id)
        ir_default.set('res.config.settings', 'door_product_id', self.door_product_id.id)
        ir_default.set('res.config.settings', 'temprature_product_id', self.temprature_product_id.id)
        ir_default.set('res.config.settings', 'chilled_temprature_product_id', self.chilled_temprature_product_id.id)
        ir_default.set('res.config.settings', 'custom_quality_team_id', self.custom_quality_team_id.id)
