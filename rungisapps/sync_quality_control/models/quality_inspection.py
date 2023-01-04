# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from odoo.addons import decimal_precision as dp
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class QualityInspection(models.Model):
    _name = "quality.inspection"
    _description = "Quality Inspection"
    _inherit = ['mail.thread']
    _rec_name = 'code'

    def _compute_show_lots_text(self):
        group_production_lot_enabled = self.user_has_groups('stock.group_production_lot')
        for inspection in self:
            inspection.show_lots_text = False
            if inspection.picking_id and group_production_lot_enabled and inspection.picking_id.picking_type_id.use_create_lots \
                    and not inspection.picking_id.picking_type_id.use_existing_lots:
                inspection.show_lots_text = True

    code = fields.Char('Reference', copy=False, default=lambda self: _('New'),
                       readonly=True, required=True)
    alert_ids = fields.One2many('quality.control.alert', 'quality_inspection_id', string='Alerts')
    name = fields.Char('Name', required=False)
    point_id = fields.Many2one('quality.control.point', string='Control Point')
    quality_inspection_line_ids = fields.One2many('quality.inspection.line', 'quality_inspection_id',
                                                  string='Inspection Lines')
    product_id = fields.Many2one('product.product', 'Product',
                                 domain="[('product_tmpl_id', '=', product_tmpl_id)]", required=True)
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', required=False,
                                      domain="[('type', 'in', ['consu', 'product'])]")
    picking_id = fields.Many2one('stock.picking', 'Operation')
    user_id = fields.Many2one('res.users', 'Responsible', track_visibility='onchange')
    team_id = fields.Many2one('quality.control.alert.team', 'Team', required=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    note = fields.Html('Note', readonly=True)
    state = fields.Selection([('none', 'To do'), ('pass', 'Passed'), ('fail', 'Failed')],
                             string='Status', track_visibility='onchange', default='none', copy=False)
    lot_id = fields.Many2one('stock.production.lot', 'Lot')
    lot_name = fields.Char('Lot/Serial Number Name')
    product_tracking = fields.Selection(related='product_id.tracking')
    inspection_type = fields.Selection([('incoming', 'Incoming Inspection'), ('outgoing', 'Outgoing Inspection'),
                                        ('in_progress', 'In-progress Inspection'), ('final', 'Final Inspection')],
                                       string='Inspection Type', track_visibility='onchange', copy=False)
    purchase = fields.Char("Purchase", related="picking_id.group_id.name", store="True")
    show_lots_text = fields.Boolean(compute='_compute_show_lots_text', default=False)

    @api.onchange('product_tmpl_id')
    def onchange_product_tmpl_id(self):
        self.product_id = self.product_tmpl_id.product_variant_ids.ids and self.product_tmpl_id.product_variant_ids[0]

    @api.onchange('point_id')
    def onchange_point_id(self):
        self.quality_point_line_ids = False
        if self.point_id:
            self.team_id = self.point_id.team_id.id

    @api.multi
    def do_fail(self):
        self.ensure_one()
        self.state = 'fail'

    @api.multi
    def do_pass(self):
        self.ensure_one()
        self.state = 'pass'

    @api.model
    def create(self, values):
        if 'code' not in values or values['code'] == _('New'):
            values['code'] = self.env['ir.sequence'].next_by_code('quality.inspection') or _('New')
        return super(QualityInspection, self).create(values)

    @api.multi
    def get_lot_id(self):
        self.ensure_one()
        return self.env['stock.production.lot'].search([('product_id', '=', self.product_id.id), ('name', '=', self.lot_name)], limit=1).id


class QualityInspectionLine(models.Model):
    _name = "quality.inspection.line"
    _description = "Quality Inspection Line"
    _inherit = ['mail.thread']

    code = fields.Char('Reference', copy=False, default=lambda self: _('New'),
                       readonly=True, required=True)
    name = fields.Char('Name', required=False)
    test_type_id = fields.Many2one('quality.control.point.test.type', 'Test Type', required=True,
                                   default=lambda self: self.env['quality.control.point.test.type'].search([('test_type', '=', 'choice')]))
    test_type = fields.Selection(related='test_type_id.test_type', string='Select Test Type')
    quality_inspection_id = fields.Many2one('quality.inspection', required=False)
    product_id = fields.Many2one(
        'product.product', 'Product Variant',
        domain="[('product_tmpl_id', '=', product_tmpl_id)]")
    product_tmpl_id = fields.Many2one(
        'product.template', 'Product', required=True,
        domain="[('type', 'in', ['consu', 'product'])]")
    measure = fields.Float('Measure', default=0.0, digits=dp.get_precision('Quality Tests'), track_visibility='onchange')
    measure_success = fields.Selection([('none', 'No measure'), ('pass', 'Pass'), ('fail', 'Fail')],
                                       string="Measure Success", readonly=True, store=True)
    norm_unit = fields.Many2one('uom.uom', string='Unit of Measure', ondelete='set null', index=True)
    note = fields.Html('Note')
    sequence = fields.Integer('Sequence', default=10)
    state = fields.Selection([('none', 'To do'), ('pass', 'Passed'), ('fail', 'Failed')],
                             string='Status', track_visibility='onchange', default='none', copy=False)
    picture = fields.Binary(string="Image")
    control_date = fields.Datetime('Control Date', track_visibility='onchange')
    failure_message = fields.Html('Failure Message')
    warning_message = fields.Text('Warning Message')
    norm = fields.Float('Norm', digits=dp.get_precision('Quality Tests'))
    tolerance_min = fields.Float('Min Tolerance', digits=dp.get_precision('Quality Tests'))
    tolerance_max = fields.Float('Max Tolerance', digits=dp.get_precision('Quality Tests'))
    product_tracking = fields.Selection(related='product_id.tracking')
    lot_id = fields.Many2one('stock.production.lot', 'Lot')
    lot_name = fields.Char('Lot/Serial Number Name')
    inspection_state = fields.Selection(related='quality_inspection_id.state', string='Inspection State')
    control_point_line_id = fields.Many2one('quality.control.point.line', ondelete='cascade')
    show_lots_text = fields.Boolean(related='quality_inspection_id.show_lots_text', default=False)
    move_line_id = fields.Many2one('stock.move.line', 'Move Line')

    @api.onchange('lot_name', 'lot_id')
    def onchange_serial_number(self):
        """
            Onchange method for lot id and lot name and check it is correct or not
        """
        res = {}
        context = dict(self.env.context or {})
        if self.product_id.tracking != 'none' and self.quality_inspection_id and self.quality_inspection_id.point_id.detailed_quality_inspection and \
                self.quality_inspection_id and context.get('picking_id'):
            message = None
            picking_id = self.env['stock.picking'].browse(context['picking_id'])
            if self.lot_id and not(any(picking_id.move_line_ids_without_package.filtered(lambda m: m.lot_id.id == self.lot_id.id and m.product_id.id == self.product_id.id))):
                message = _('Please select correct the lot number. It does not match with Picking Operation.')
            if self.lot_name and not(any(picking_id.move_line_ids_without_package.filtered(lambda m: m.lot_name == self.lot_name and m.product_id.id == self.product_id.id))):
                message = _('Please enter correct the lot number. It does not match with Picking Operation.')
            if message:
                res['warning'] = {'title': _('Warning'), 'message': message}
        return res

    def check_lot_serial_number(self):
        context = dict(self.env.context or {})
        if self.product_id.tracking != 'none' and self.quality_inspection_id and self.quality_inspection_id.point_id.detailed_quality_inspection and \
                self.quality_inspection_id and context.get('picking_id'):
            picking_id = self.env['stock.picking'].browse(context['picking_id'])
            # Added Move lines as dynamic. If Move entire package is enabled, in picking type move_line_ids_without_package dont have values.
            #Filtered values from move lines based on product, lot and picking.
            move_lines = self.env['stock.move.line']
            if picking_id.move_line_ids_without_package:
                move_lines = picking_id.move_line_ids_without_package
            else:
                move_lines = self.env['stock.move.line'].search([('lot_id', '=', self.lot_id.id),('product_id', '=', self.product_id.id),('picking_id','=', picking_id.id)])
            if self.lot_id and not(any(move_lines.filtered(lambda m: m.lot_id.id == self.lot_id.id and m.product_id.id == self.product_id.id))):
                raise ValidationError(_('Please select correct the lot number. It does not match with Picking Operation.'))
            move_lines_name = self.env['stock.move.line']
            if picking_id.move_line_ids_without_package:
                move_lines_name = picking_id.move_line_ids_without_package
            else:
                move_lines_name = self.env['stock.move.line'].search([('lot_name', '=', self.lot_name),('product_id', '=', self.product_id.id),('picking_id','=', picking_id.id)])

            if self.lot_name and not(any(move_lines_name.filtered(lambda m: m.lot_name == self.lot_name and m.product_id.id == self.product_id.id))):
                raise ValidationError(_('Please enter correct the lot number. It does not match with Picking Operation.'))

    @api.multi
    def do_alert(self):
        self.ensure_one()
        action = self.env.ref('sync_quality_control.quality_control_alert_action_small').read()[0]
        # action['res_id'] = self.quality_inspection_id.alert_ids.id
        action['context'] = {
            'default_product_id': self.product_id.id,
            'default_product_tmpl_id': self.product_id.product_tmpl_id.id,
            'default_quality_inspection_id': self.quality_inspection_id.id,
            'default_quality_inspection_line_id': self.id,
            'default_lot_id': self.lot_id.id,
            'default_lot_name': self.lot_name,
            'default_picking_id': self.quality_inspection_id.picking_id.id
        }
        return action

    @api.model
    def create(self, values):
        if 'code' not in values or values['code'] == _('New'):
            values['code'] = self.env['ir.sequence'].next_by_code('quality.inspection.line') or _('New')
        return super(QualityInspectionLine, self).create(values)

    @api.multi
    def do_measure(self):
        self.ensure_one()
        self.check_lot_serial_number()
        context = dict(self.env.context or {})
        if not context.get('line_ids'):
            context.update({'line_ids': self.ids})
            self.env.context = context
        context = context = dict(self.env.context or {})
        if not context.get('picking_id'):
            context.update({'picking_id': self.quality_inspection_id and self.quality_inspection_id.picking_id and self.quality_inspection_id.picking_id.id})
            self.env.context = context
        if self.tolerance_min == 0.00 and self.tolerance_max == 0.00 and self.measure != self.norm:
            self.write({'measure_success': 'fail',
                        'warning_message': _('You measured %.2f %s and it should be same as %.2f %s.') %
                                           (self.measure, self.norm_unit.name, self.norm, self.norm_unit.name)
                        })
            return {
                'name': _('Quality Inspection Failed'),
                'type': 'ir.actions.act_window',
                'res_model': 'quality.inspection.line',
                'view_mode': 'form',
                'view_id': self.env.ref('sync_quality_control.quality_inspection_line_view_form_failure').id,
                'target': 'new',
                'res_id': self.id,
                'context': self.env.context,
            }
        elif self.measure != self.norm and (self.measure < self.tolerance_min or self.measure > self.tolerance_max):
            self.write({'measure_success': 'fail',
                        'warning_message': _('You measured %.2f %s and it should be between %.2f and %.2f %s.') %
                                           (self.measure, self.norm_unit.name, self.tolerance_min,
                                            self.tolerance_max, self.norm_unit.name)
                        })
            return {
                'name': _('Quality Inspection Failed'),
                'type': 'ir.actions.act_window',
                'res_model': 'quality.inspection.line',
                'view_mode': 'form',
                'view_id': self.env.ref('sync_quality_control.quality_inspection_line_view_form_failure').id,
                'target': 'new',
                'res_id': self.id,
                'context': self.env.context,
            }
        else:
            self.write({'measure_success': 'pass'})
            return self.do_pass()

    @api.multi
    def correct_measure(self):
        self.ensure_one()
        line_ids = []
        if self._context.get('line_ids'):
            for context in self._context.get('line_ids'):
                line_ids.append(context)
        if line_ids:
            action = self.env.ref('sync_quality_control.quality_inspection_line_action_small').read()[0]
            action['context'] = {'line_ids': line_ids}
            action['res_id'] = line_ids[0]
            return action
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def do_fail(self):
        self.ensure_one()
        self.check_lot_serial_number()
        self.write({'state': 'fail', 'control_date': datetime.now()})
        return self.redirect_on_pass_fail()

    @api.multi
    def quality_inspection_wizard(self, line_ids):
        if line_ids:
            action = self.env.ref('sync_quality_control.quality_inspection_line_action_small').read()[0]
            action['context'] = {'line_ids': line_ids}
            action['res_id'] = line_ids[0]
            return action
        if self._context.get('quality_inspection_id'):
            inspections = self._context.get('quality_inspection_id')
            if isinstance(inspections, str):
                inspections = int(inspections)
            quality_inspection_ids = self.env['quality.inspection'].browse(self._context['quality_inspection_id'])
            for inspection in quality_inspection_ids:
                if all(line.state == 'pass' for line in inspection.quality_inspection_line_ids):
                    inspection.do_pass()
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def redirect_on_pass_fail(self):
        line_ids = []
        if self._context.get('line_ids'):
            for context in self._context.get('line_ids'):
                con = self.browse(context)
                if self.id != context:
                    con = self.browse(context)
                    if self.lot_id and self.quality_inspection_id.id == con.quality_inspection_id.id:
                        con.quality_inspection_id.lot_id = self.lot_id
                        con.update({"lot_id": self.lot_id})
                    if self.lot_name and self.quality_inspection_id.id == con.quality_inspection_id.id:
                        con.quality_inspection_id.lot_name = self.lot_name
                        con.update({"lot_name": self.lot_name})
                    line_ids.append(context)
                con.quality_inspection_id.lot_id = self.lot_id
                con.quality_inspection_id.lot_name = self.lot_name
            return self.quality_inspection_wizard(line_ids)

    @api.multi
    def create_new_inspection(self):
        self.ensure_one()
        context = dict(self.env.context or {})
        if context.get('picking_id') and self.quality_inspection_id and self.quality_inspection_id.point_id:
            picking_id = self.env['stock.picking'].browse(context['picking_id'])
            quality_inspection_id = self.env['quality.inspection'].create({
                            'picking_id': int(context['picking_id']),
                            'point_id': self.quality_inspection_id.point_id.id,
                            'team_id': self.quality_inspection_id.point_id.team_id.id,
                            'lot_id': self.lot_id.id,
                            'lot_name': self.lot_name,
                            'product_id': self.quality_inspection_id.product_id.id,
                            'product_tmpl_id': self.quality_inspection_id.point_id.product_tmpl_id
                                              and self.quality_inspection_id.point_id.product_tmpl_id.id,
                            'inspection_type': 'incoming'
                        })
            quality_inspection_id.onchange_point_id()
            if len(self.quality_inspection_id.point_id.quality_control_point_line_ids) > 0:
                for line in self.quality_inspection_id.point_id.quality_control_point_line_ids:
                    if line.inspection_execute_now(quality_inspection_id):
                        inspection_line_data = ({
                            'name': line.name,
                            'control_point_line_id': line.id,
                            'test_type_id': line.test_type_id.id,
                            'quality_inspection_id': quality_inspection_id.id,
                            'failure_message': line.failure_message,
                            'product_tmpl_id': quality_inspection_id.product_tmpl_id.id,
                            'product_id': self.quality_inspection_id.product_id.id,
                            'norm_unit': line.norm_unit.id,
                            'norm': line.norm,
                            'lot_id': self.lot_id.id,
                            'lot_name': self.lot_name,
                            'tolerance_min': line.tolerance_min,
                            'tolerance_max': line.tolerance_max,
                        })
                        quality_inspection_line_ids = self.env['quality.inspection.line'].create(inspection_line_data)
                picking_id.quality_inspection_ids = [(4, quality_inspection_id.id)]
            else:
                raise ValidationError(_('You need to be configure at least one control point line.'))
            if quality_inspection_id:
                for line in quality_inspection_id.quality_inspection_line_ids:
                    action_rec = self.env.ref('sync_quality_control.quality_inspection_line_action_small')
                    if action_rec:
                        action = action_rec.read([])[0]
                        action['context'] = {'line_ids': quality_inspection_id.quality_inspection_line_ids.ids, 'quality_inspection_id': quality_inspection_id.ids, 'picking_id': picking_id.id}
                        action['res_id'] = line.id
                        return action

    @api.multi
    def do_pass(self):
        self.ensure_one()
        self.check_lot_serial_number()
        self.write({'state': 'pass',
                    'control_date': datetime.now()})
        return self.redirect_on_pass_fail()
