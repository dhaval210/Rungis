# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, SUPERUSER_ID


class QualityControlAlertStage(models.Model):
    _name = "quality.control.alert.stage"
    _description = "Quality Control Alert Stage"
    _order = "sequence, id"
    _fold_name = 'folded'

    name = fields.Char('Name', required=True)
    sequence = fields.Integer('Sequence', default=10)
    folded = fields.Boolean('Folded', default=False)
    done = fields.Boolean('Alert Processed', default=False)
    scraped = fields.Boolean('Scraped', default=False)


class QualityFailReason(models.Model):
    _name = "quality.fail.reason"
    _description = "Quality Fail Reason"

    name = fields.Char('Name', required=True)


class QualityControlAlert(models.Model):
    _name = "quality.control.alert"
    _description = "Quality Control Alert"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "code"

    code = fields.Char('Reference', copy=False, default=lambda self: _('New'),
                       readonly=True, required=True)
    stage_id = fields.Many2one('quality.control.alert.stage', 'Stage',
        default=lambda self: self.env['quality.control.alert.stage'].search([], limit=1).id, track_visibility="onchange")
    product_id = fields.Many2one(
        'product.product', 'Product',
        domain="[('product_tmpl_id', '=', product_tmpl_id)]", required=True)
    product_tmpl_id = fields.Many2one(
        'product.template', 'Product Template', required=False,
        domain="[('type', 'in', ['consu', 'product'])]")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    picking_id = fields.Many2one('stock.picking', 'Operation')
    quality_inspection_id = fields.Many2one('quality.inspection', domain="[('product_tmpl_id','=',product_tmpl_id)]")
    quality_inspection_line_id = fields.Many2one('quality.inspection.line', string="Inspection Parameter",
                                                 domain="[('quality_inspection_id', '=', quality_inspection_id), "
                                                        "('state', '=', 'fail')]")
    team_id = fields.Many2one(
        'quality.control.alert.team', 'Team', required=True,
        default=lambda x: x.env['quality.control.alert.team'].search([], limit=1))
    user_id = fields.Many2one('res.users', 'Responsible', track_visibility='onchange')
    action_corrective = fields.Text('Corrective Action')
    action_preventive = fields.Text('Preventive Action')
    description = fields.Text('Description')
    reason_ids = fields.Many2many('quality.fail.reason', string="Reason",required=True)
    lot_id = fields.Many2one('stock.production.lot', 'Lot', readonly=True)
    lot_name = fields.Char('Lot/Serial Number Name')
    readonly_field = fields.Boolean('Readonly', compute='_check_stage')

    @api.multi
    def _check_stage(self):
        for record in self:
            record.readonly_field = False
            if record.stage_id.done or record.stage_id.scraped:
                record.readonly_field = True

    @api.multi
    def action_send_mail(self):
        try:
            template_id = self.env.ref('sync_quality_control.email_template_quality_alert')
        except ValueError:
            template_id = False
        if template_id:
            template_id.send_mail(self.id, force_send=True, raise_exception=False, email_values=None)

    @api.model
    def create(self, values):
        values['code'] = self.env['ir.sequence'].next_by_code('quality.control.alert')
        return super(QualityControlAlert, self).create(values)
