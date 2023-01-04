from odoo import api, fields, models


class ResGenericLabel(models.Model):
    _name = 'res.generic.label'
    _description = 'generic label configuration'

    field_id = fields.Many2one(comodel_name='ir.model.fields', domain="[('model_id', '=', 'stock.picking')]")
    condition = fields.Selection(selection=[
        ('==', '='),
        ('<', '<'),
        ('>', '>'),
        ('!=', '!='),
    ])
    value = fields.Char()
    report_id = fields.Many2one(comodel_name='ir.actions.report')
