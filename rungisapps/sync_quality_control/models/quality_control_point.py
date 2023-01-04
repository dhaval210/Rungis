# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import random
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError


class QualityControlPointTestType(models.Model):
    _name = "quality.control.point.test.type"
    _description = "Different type of testing parameter define here"

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    test_type = fields.Selection([('choice', 'Choice'), ('image', 'Image'), ('measure', 'Measure')],
                                 string='Test Type', default='choice')


class QualityControlAlertTeam(models.Model):
    _name = "quality.control.alert.team"
    _description = "Different type of team which can solved quality alert"
    _inherit = ['mail.alias.mixin','mail.thread']
    _order = "sequence, id"

    name = fields.Char('Name', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    sequence = fields.Integer('Sequence', default=10)
    color = fields.Integer('Color', default=1)
    alias_id = fields.Many2one('mail.alias', string='Alias', ondelete="restrict", required=True)

    def get_alias_model_name(self, values):
        return values.get('alias_model', 'quality.control.alert')

    def get_alias_values(self):
        values = super(QualityControlAlertTeam, self).get_alias_values()
        values['alias_defaults'] = {'team_id': self.id}
        return values


class QualityControlPoint(models.Model):
    _name = "quality.control.point"
    _description = "Quality Control Point"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence'

    @api.model
    def default_get(self, fields):
        rec = super(QualityControlPoint, self).default_get(fields)
        detailed_quality_inspection = self.env["ir.config_parameter"].sudo().get_param("sync_quality_control.always_detailed_quality_inspection")
        rec.update({'detailed_quality_inspection': detailed_quality_inspection})
        return rec

    def _get_default_team_id(self):
        return self.env['quality.control.alert.team'].search([], limit=1)

    code = fields.Char('Reference', copy=False, default=lambda self: _('New'),
                       readonly=True, required=True)
    sequence = fields.Integer('Sequence', default=5)
    name = fields.Char('Name', required=True)
    team_id = fields.Many2one('quality.control.alert.team', 'Team',
                              default=_get_default_team_id, required=True)
    product_id = fields.Many2one('product.product', 'Product Variant',
                                 domain="[('product_tmpl_id', '=', product_tmpl_id)]")
    product_tmpl_id = fields.Many2one('product.template', 'Product', required=True,
                                      domain="[('type', 'in', ['consu', 'product'])]")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    active = fields.Boolean('Active', default=True)
    reason = fields.Html('Note')
    picking_type_id = fields.Many2one('stock.picking.type', "Operation Type", required=True)
    quality_control_point_line_ids = fields.One2many('quality.control.point.line', 'quality_control_point_id')
    version_id = fields.Many2one('quality.control.point.version', 'Version')
    is_restrict = fields.Boolean('Is Restrict', default=False, help='Restrict to validate opration, if inspection is fail')
    detailed_quality_inspection = fields.Boolean('Detailed Quality Inspection', default=False)

    @api.multi
    @api.constrains('id', 'product_tmpl_id', 'quality_control_point_line_ids')
    def check_control_point_line(self):
        """
            Constraints for the record create with blank inspection line.
        """
        for rec in self:
            if not self._context.get('from_copy', False) and len(rec.quality_control_point_line_ids) == 0:
                raise ValidationError(_('You need to be configure at least one control point line.'))

    @api.multi
    def copy(self, default=None):
        return super(QualityControlPoint, self.with_context(from_copy=True)).copy(default)

    @api.model
    def create(self, values):
        values['code'] = self.env['ir.sequence'].next_by_code('quality.control.point')
        return super(QualityControlPoint, self).create(values)

    @api.multi
    def write(self, values):
        allow_config_control_point = self.env['ir.config_parameter'].sudo().get_param(
            'sync_quality_control.module_quality_control_allow')
        if not allow_config_control_point and values.get('quality_control_point_line_ids'):
            inspection = self.env['quality.inspection'].search([('point_id', '=', self.id)])
            if inspection:
                raise ValidationError(_('You can not change control point line after any inspections of this '
                                        'control point. \n You need to create new control point version of '
                                        'same product.'))
        return super(QualityControlPoint, self).write(values)

    @api.onchange('product_tmpl_id')
    def onchange_product_tmpl_id(self):
        self.product_id = self.product_tmpl_id.product_variant_ids.ids and self.product_tmpl_id.product_variant_ids[0]


class QualityControlPointLine(models.Model):
    _name = "quality.control.point.line"
    _description = "Quality Control Point Line"
    _order = "sequence, id"

    code = fields.Char('Reference', copy=False, default=lambda self: _('New'),
                       readonly=True, required=True)
    name = fields.Char('Name', required=True)
    quality_control_point_id = fields.Many2one('quality.control.point', required=True)
    test_type_id = fields.Many2one('quality.control.point.test.type', 'Test Type', required=True,
                                   default=lambda self: self.env['quality.control.point.test.type'].search(
                                       [('test_type', '=', 'choice')]))
    test_type = fields.Selection(related='test_type_id.test_type', string='Select Test Type')
    measure_frequency_type = fields.Selection([('all', 'All Operations'), ('random', 'Randomly'),
                                               ('periodical', 'Periodically')], string="Frequency Type",
                                              default='all', required=True)
    measure_frequency_value = fields.Float('Percentage')
    measure_frequency_unit_value = fields.Integer('Frequency')
    measure_frequency_unit = fields.Selection([('day', 'Day(s)'), ('week', 'Week(s)'), ('month', 'Month(s)')],
                                              default="day")
    norm = fields.Float('Norm', digits=dp.get_precision('Quality Tests'))
    tolerance_min = fields.Float('Min Tolerance', digits=dp.get_precision('Quality Tests'))
    tolerance_max = fields.Float('Max Tolerance', digits=dp.get_precision('Quality Tests'))
    norm_unit = fields.Many2one('uom.uom', string='Unit of Measure',
                                ondelete='set null', index=True)
    note = fields.Html('Note')
    failure_message = fields.Html('Failure Message')
    sequence = fields.Integer('Sequence', default=10)
    limit = fields.Integer('Limit')

    @api.constrains('norm', 'tolerance_min', 'tolerance_max')
    def constrain_tolerance(self):
        for control_point_line in self:
            if control_point_line.norm and control_point_line.tolerance_min and control_point_line.norm < control_point_line.tolerance_min:
                raise ValidationError(_("Minimum tolerance should be less than Norm"))
            elif control_point_line.norm and control_point_line.tolerance_max and control_point_line.norm > control_point_line.tolerance_max:
                raise ValidationError(_("Maximum tolerance should be grater than Norm"))

    @api.multi
    def inspection_execute_now(self, quality_inspection_id):
        self.ensure_one()
        if self.measure_frequency_type == 'all':
            return True
        elif self.measure_frequency_type == 'random':
            return random.random() < self.measure_frequency_value / 100.0
        elif self.measure_frequency_type == 'periodical':
            delta = False
            if self.measure_frequency_unit == 'day':
                delta = relativedelta(days=self.measure_frequency_unit_value)
            elif self.measure_frequency_unit == 'week':
                delta = relativedelta(weeks=self.measure_frequency_unit_value)
            elif self.measure_frequency_unit == 'month':
                delta = relativedelta(months=self.measure_frequency_unit_value)
            date_previous = datetime.today() - delta
            inspection_ids = self.env['quality.inspection'].search([('point_id', '=', self.quality_control_point_id.id),
                                                                    ('id', '!=', quality_inspection_id.id)])
            inspection_line_ids = False
            count = 0
            for inspection in inspection_ids:
                count += 1
                inspection_line_ids = self.env['quality.inspection.line'].search([
                    ('id', 'in', inspection.quality_inspection_line_ids.ids),
                    ('create_date', '>=', date_previous.strftime(DEFAULT_SERVER_DATETIME_FORMAT))])
            return False if inspection_line_ids or count > self.limit else True
        return False

    @api.model
    def create(self, values):
        values['code'] = self.env['ir.sequence'].next_by_code('quality.control.point.line')
        return super(QualityControlPointLine, self).create(values)

    @api.multi
    def unlink(self):
        for record in self:
            inspection_line_ids = self.env['quality.inspection.line'].search([('control_point_line_id', '=',
                                                                               record.id)])
            if inspection_line_ids:
                raise ValidationError(_('You can not remove control point line after any inspections of this '
                                        'control point. \n You need to create new control point version of '
                                        'same product.'))
        return super(QualityControlPointLine, self).unlink()


class QualityControlPointVersion(models.Model):
    _name = "quality.control.point.version"
    _description = "Quality Control Point Version"

    name = fields.Char('Name', required=True)
