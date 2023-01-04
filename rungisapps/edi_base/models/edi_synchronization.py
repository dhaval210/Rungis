# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, SUPERUSER_ID


class SynchronizationStage(models.Model):

    _name = 'edi.synchronization.stage'
    _description = 'Synchronization Stage'

    def _get_default_integration_ids(self):
        default_integration_id = self.env.context.get('default_integration_id')
        return [default_integration_id] if default_integration_id else None

    name = fields.Char(required=True, translate=True, string='Stage Name')
    sequence = fields.Integer(default=1)
    color = fields.Integer(string='Color Index')
    state = fields.Selection(selection=[
        ('new', 'New'),
        ('done', 'Done'),
        ('fail', 'Fail'),
        ('cancel', 'Cancel')
    ], required=True, string='State')
    integration_ids = fields.Many2many(
        comodel_name='edi.integration',
        relation='integration_synchronization_stage_rel',
        column1='stage_id',
        column2='integration_id',
        default=lambda self: self._get_default_integration_ids(),
        string='Integrations'
    )

    _sql_constraints = [
        ('state_uniq', 'unique (state)', 'The state must be unique !'),
    ]


class Synchronization(models.Model):

    _name = 'edi.synchronization'
    _description = 'Synchronization'

    def _selection_resource_model(self):
        models = self.env['ir.model'].search([])
        return [(model.model, model.name) for model in models]

    def _get_default_stage_id(self, *args, **kwargs):
        integration_id = self.env.context.get('default_integration_id')
        if not integration_id:
            return False

        return self.env['edi.synchronization.stage'].search([
            ('state', '=', 'new'),
            ('integration_ids', 'in', [integration_id])
        ], limit=1).id

    def _read_group_stage_ids(self, stages, domain, order):
        search_domain = []
        if 'default_integration_id' in self.env.context:
            search_domain = [
                ('integration_ids', 'in', [self.env.context['default_integration_id']])
            ]
        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    name = fields.Char(readonly=True, required=True)
    filename = fields.Char(readonly=True)

    stage_id = fields.Many2one(
        comodel_name='edi.synchronization.stage',
        group_expand='_read_group_stage_ids',
        default=_get_default_stage_id,
        domain="[('integration_ids', '=', integration_id)]",
        string='Status'
    )
    stage_state = fields.Selection(
        related='stage_id.state',
        store=True,
        readonly=True,
        string='State'
    )

    integration_id = fields.Many2one('edi.integration', required=True, string='Integration')
    synchronization_type = fields.Selection(
        related='integration_id.integration_type',
        store=True,
        readonly=True,
        string='Type'
    )
    content_type = fields.Selection(
        related='integration_id.synchronization_content_type',
        store=True,
        readonly=True,
        string='Content type'
    )
    res_model_id = fields.Many2one(
        related='integration_id.res_model_id',
        store=True,
        string='Resource model'
    )

    res_model = fields.Char(related='res_model_id.model', string='Resouce model name')
    res_id = fields.Integer(string='Resource ID')
    resource_reference = fields.Reference(
        selection='_selection_resource_model',
        compute='_compute_resource_reference',
        string='Resource reference'
    )

    has_records = fields.Boolean(compute='_compute_has_records', string='Has records?')

    synchronization_date = fields.Datetime(readonly=True, string='Synchronized on')
    content = fields.Text(readonly=True)

    error_ids = fields.One2many('edi.synchronization.error', 'synchronization_id', string='synchronization_id')
    errors_count = fields.Integer(_compute='_compute_errors_count', string='# errors')

    _sql_constraints = [
        (
            'name_integration_id_uniq',
            'unique (name, integration_id)',
            'The name must be unique per integration!'
        )
    ]

    @api.depends('error_ids')
    def _compute_errors_count(self):
        for synchronization in self:
            synchronization.errors_count = len(synchronization.error_ids)

    @api.depends('res_model', 'res_id')
    def _compute_resource_reference(self):

        for synchronization in self:

            model_name = synchronization.res_model
            res_id = synchronization.res_id or 0

            synchronization.resource_reference = '%s,%s' % (model_name, res_id)

    def _compute_has_records(self):
        for synchronization in self:
            synchronization.has_records = bool(synchronization.res_id)

    @api.multi
    def open_integration(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Integration',
            'res_model': 'edi.integration',
            'res_id': self.integration_id.id,
            'view_mode': 'form'
        }

    @api.multi
    def open_resource_records(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Open records',
            'res_model': self.res_model,
            'res_id': self.res_id,
            'view_mode': 'form'
        }

    def _get_method_name(self):
        return '_%s_%s_%s_synchronization_process'

    def _get_method_values(self):
        return (
            self.res_model_id.model.replace('.', '_'),
            self.content_type,
            self.integration_id.integration_type
        )

    def _process(self, synchronization_item):
        """
        """

        self.ensure_one()

        method_string = self._get_method_name()
        method_values = self._get_method_values()

        getattr(self, method_string % method_values)(synchronization_item)


class SynchronizationError(models.Model):

    _name = 'edi.synchronization.error'
    _description = 'Synchronization Error'

    synchronization_id = fields.Many2one(
        comodel_name='edi.synchronization',
        on_delete='cascade',
        string='Synchronization'
    )
    activity = fields.Char()
    description = fields.Text()
