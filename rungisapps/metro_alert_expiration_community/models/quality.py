# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime

from odoo import api, fields, models


class QualityControlPointLine(models.Model):
    _inherit = "quality.control.point.line"

    time_ratio = fields.Float("Max allowed use time ratio")


class QualityControlPointTestType(models.Model):
    _inherit = "quality.control.point.test.type"

    test_type = fields.Selection(
        selection_add=[('time_ratio', 'Use time ratio')])

    @api.multi
    def check_execute_now(self):
        if self.test_type == 'time_ratio':
            return False
        else:
            return True


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def action_done(self):
        res = super(StockPicking, self).action_done()
        for lot in self.mapped('move_line_ids.lot_id'):
            quality_point = self.env[
                'quality.control.point'].sudo().search([
                    ('picking_type_id', '=', self.picking_type_id.id),
                    ('quality_control_point_line_ids.test_type', '=','time_ratio'),
                    ('product_tmpl_id', '=', lot.product_id.product_tmpl_id.id)],limit=1)
            if quality_point:
                if lot.use_date:
                    for q_point in quality_point.quality_control_point_line_ids:
                        if q_point.test_type == 'time_ratio':
                            if fields.Date.from_string(
                                    lot.use_date) <= datetime.date.today() or (
                                    fields.Date.from_string(
                                            lot.use_date) - datetime.date.today()).days / float(
                                    lot.product_id.product_tmpl_id.use_time) < q_point.time_ratio:
                                alert = self.env[
                                    'quality.control.alert'].sudo().create({
                                        'partner_id': self.partner_id.id,
                                        'product_id': lot.product_id.id,
                                        'product_tmpl_id': lot.product_id.product_tmpl_id.id,
                                        'lot_id': lot.id,
                                        'reason_ids': [(6, 0, self.env.ref(
                                            'metro_alert_expiration_community.reason_time_ratio').ids)],
                                        'company_id': self.company_id.id,
                                    })
        return res

