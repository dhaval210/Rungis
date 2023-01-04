# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.multi
    def action_view_control_points_request(self):
        get_control_points_ids = self.mapped('control_points_ids')
        action = self.env.ref('sync_quality_control.quality_control_point_action').read()[0]
        self.points_count = len(get_control_points_ids)
        if len(get_control_points_ids) > 1:
            action['domain'] = [('id', 'in', get_control_points_ids.ids)]
        elif len(get_control_points_ids) == 1:
            action['views'] = [(self.env.ref('sync_quality_control.quality_control_point_view_form').id, 'form')]
            action['res_id'] = get_control_points_ids.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    points_count = fields.Integer(string='# of Control Points')
    control_points_ids = fields.One2many('quality.control.point', 'product_id', string="Control Points")
