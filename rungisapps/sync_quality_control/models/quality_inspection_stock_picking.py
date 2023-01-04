# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    quality_inspection_ids = fields.One2many('quality.inspection', 'picking_id')
    quality_inspection_todo = fields.Boolean(compute='_compute_inspection')
    alert_ids = fields.One2many('quality.control.alert', 'picking_id')
    quality_control_alert_count = fields.Integer(compute='_compute_quality_alert_count')

    @api.multi
    def _compute_quality_alert_count(self):
        for production in self:
            production.quality_control_alert_count = len(production.alert_ids)

    @api.multi
    def _compute_inspection(self):
        for record in self:
            for move_id in record.move_lines:
                if move_id.quality_inspection_todo:
                    record.quality_inspection_todo = True
                    return True
            record.quality_inspection_todo = False
        return False

    @api.multi
    def get_line_data(self, line, quality_inspection_id):
        inspection_line_data = ({
                        'name': line.name,
                        'test_type_id': line.test_type_id.id,
                        'quality_inspection_id': quality_inspection_id.id,
                        'failure_message': line.failure_message,
                        'product_tmpl_id': quality_inspection_id.product_id.product_tmpl_id.id,
                        'product_id': quality_inspection_id.product_id.id,
                        })
        return inspection_line_data

    @api.multi
    def quality_inspection_wizard(self, line_ids_list, line):
        action_rec = self.env.ref('sync_quality_control.quality_inspection_line_action_small')
        if action_rec:
            action = action_rec.read([])[0]
            action['context'] = {'line_ids': line_ids_list, 'line': line}
            action['res_id'] = line.id
            return action

    @api.multi
    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        if self.move_ids_without_package:
            move_ids = self.move_ids_without_package
        elif self.move_lines:
            move_ids = self.move_lines
        if move_ids:
            for move in move_ids:
                points = self.env['quality.control.point'].search([('product_id', '=', move.product_id.id), ('picking_type_id', '=', move.picking_id.picking_type_id.id)], order='sequence ASC')
                if points:
                    point = points[0]
                    if point[0].is_restrict:
                        if not self.quality_inspection_ids.filtered(lambda l: l.product_id.id == move.product_id.id):
                            raise UserError(_('It\'s seems like you have not inspect the quality of product "%s"' % move.product_id.name))
                        if self.quality_inspection_ids.filtered(lambda l: l.product_id.id == move.product_id.id and l.state != 'pass'):
                            raise UserError(_('Kindly check quality inspection status of product "%s %s" it should be passed.' % (move.product_id.name, move.product_id.code)))
        for inspection_line in self.quality_inspection_ids.filtered(lambda q: q.lot_name and not q.lot_id):
            inspection_line.lot_id = inspection_line.get_lot_id()
            for line in inspection_line.quality_inspection_line_ids:
                line.lot_id = inspection_line.lot_id.id
        return res


class StockMove(models.Model):
    _inherit = "stock.move"

    quality_inspection_todo = fields.Boolean(compute='_compute_inspection')

    @api.multi
    def _compute_inspection(self):
        for record in self:
            todo = False
            points = self.env['quality.control.point'].search([('product_id', '=', record.product_id.id),
                                                               ('picking_type_id', '=', record.picking_id.picking_type_id.id)])
            if not points:
                points = self.env['quality.control.point'].search([('product_id', '=', False),
                                                                   ('product_tmpl_id', '=', record.product_id.product_tmpl_id.id),
                                                                   ('picking_type_id', '=', record.picking_id.picking_type_id.id)])
                if points:
                    todo = True
            else:
                todo = True
            record.quality_inspection_todo = todo

    @api.multi
    def inspection_quality_line(self):
        for move_id in self:
            quality_inspection_line_obj = self.env['quality.inspection.line']
            line_ids_list, quality_inspections = [], []
            quality_inspection_line_ids = False
            points = self.env['quality.control.point'].search([('product_id', '=', move_id.product_id.id),
                                                               ('picking_type_id', '=', move_id.picking_id.picking_type_id.id)
                                                               ], order='sequence ASC')
            if not points:
                points = self.env['quality.control.point'].search([('product_id', '=', False),
                                                                   ('product_tmpl_id', '=', move_id.product_id.product_tmpl_id.id),
                                                                   ('picking_type_id', '=', move_id.picking_id.picking_type_id.id)
                                                                   ], order='sequence ASC')
            if points:
                point = points[0]
                point_move_lines = move_id
                if point.detailed_quality_inspection:
                    point_move_lines = move_id.move_line_ids
                picking_inspections = move_id.picking_id.quality_inspection_ids.filtered(lambda q: q.state == 'none' and q.product_id.id == move_id.product_id.id)
                if picking_inspections:
                    quality_inspections += picking_inspections.ids
                    for picking_inspection in picking_inspections:
                        for picking_inspection_line in picking_inspection.quality_inspection_line_ids.filtered(lambda p: p.state == 'none'):
                            if not picking_inspection_line.lot_id or (picking_inspection_line.lot_id and picking_inspection_line.move_line_id.lot_id.id != picking_inspection_line.lot_id.id):
                                picking_inspection_line.lot_id = picking_inspection_line.move_line_id.lot_id.id if picking_inspection_line.move_line_id and picking_inspection_line.move_line_id.lot_id else False
                                picking_inspection_line.quality_inspection_id.lot_id = picking_inspection_line.lot_id.id
                            if not picking_inspection_line.lot_name or (picking_inspection_line.lot_name and picking_inspection_line.move_line_id.lot_name != picking_inspection_line.lot_name):
                                picking_inspection_line.lot_name = picking_inspection_line.move_line_id.lot_name if picking_inspection_line.move_line_id and picking_inspection_line.move_line_id.lot_name else False
                                picking_inspection_line.quality_inspection_id.lot_name = picking_inspection_line.lot_name
                            line_ids_list += picking_inspection_line.ids
                            quality_inspection_line_obj += picking_inspection_line
                if line_ids_list == []:
                    for move_line in point_move_lines:
                        quality_inspection_id = self.env['quality.inspection'].create({'picking_id': move_id.picking_id.id,
                                                                                       'point_id': point.id,
                                                                                       'team_id': point.team_id.id,
                                                                                       'product_id': move_id.product_id.id,
                                                                                       'lot_id': move_line.lot_id.id if move_line._name == 'stock.move.line' and move_line.lot_id else False,
                                                                                       'lot_name': move_line.lot_name if move_line._name == 'stock.move.line' else False,
                                                                                       'product_tmpl_id': point.product_tmpl_id
                                                                                                          and point.product_tmpl_id.id,
                                                                                       'inspection_type': 'incoming'})
                        quality_inspection_id.onchange_point_id()
                        if len(point.quality_control_point_line_ids) > 0:
                            for line in point.quality_control_point_line_ids:
                                if line.inspection_execute_now(quality_inspection_id):
                                    inspection_line_data = ({
                                        'name': line.name,
                                        'control_point_line_id': line.id,
                                        'test_type_id': line.test_type_id.id,
                                        'quality_inspection_id': quality_inspection_id.id,
                                        'failure_message': line.failure_message,
                                        'product_tmpl_id': quality_inspection_id.product_tmpl_id.id,
                                        'lot_id': move_line.lot_id.id if move_line._name == 'stock.move.line' and move_line.lot_id else False,
                                        'lot_name': move_line.lot_name if move_line._name == 'stock.move.line' else False,
                                        'move_line_id': move_line.id if move_line._name == 'stock.move.line' else False,
                                        'product_id': move_id.product_id.id,
                                        'norm_unit': line.norm_unit.id,
                                        'norm': line.norm,
                                        'tolerance_min': line.tolerance_min,
                                        'tolerance_max': line.tolerance_max,
                                    })
                                    quality_inspection_line_ids = self.env['quality.inspection.line'].create(inspection_line_data)
                            self.quality_inspection_ids = [(4, quality_inspection_id.id)]
                            # quality_inspection_id.write({"lot_id": quality_inspection_line_ids and
                            #                                        quality_inspection_line_ids.lot_id})
                            if quality_inspection_id:
                                quality_inspections += quality_inspection_id.ids
                                line_ids_list += quality_inspection_id.quality_inspection_line_ids.ids
                                quality_inspection_line_obj += quality_inspection_id.quality_inspection_line_ids
                        else:
                            raise ValidationError(_('You need to be configure at least one control point line.'))
            for line in quality_inspection_line_obj:
                action_rec = self.env.ref('sync_quality_control.quality_inspection_line_action_small')
                if action_rec:
                    action = action_rec.read([])[0]
                    action['context'] = {'line_ids': line_ids_list, 'quality_inspection_id': quality_inspections, 'picking_id': move_id.picking_id.id}
                    action['res_id'] = line.id
                    return action
