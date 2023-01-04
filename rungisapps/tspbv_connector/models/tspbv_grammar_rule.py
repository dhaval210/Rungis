from odoo import api, fields, models


class GrammarRule(models.Model):
    _name = 'tspbv.grammar.rule'

    rule_name = fields.Char(string='Name')
    content = fields.Char(string='Content')
    constraint_id = fields.Many2one('tspbv.grammar.rule.constraint', string = 'Constraint')
    display_name = fields.Char(compute='_compute_display_name')

    @api.multi
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.rule_name

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, record.display_name))
        return res

