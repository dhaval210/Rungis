from odoo import api, fields, models


class GrammarRuleConstraint(models.Model):
    _name = 'tspbv.grammar.rule.constraint'

    min = fields.Integer('Min')
    max = fields.Integer('Max')
    decimalsmin = fields.Integer('Decimals Min')
    decimalsmax = fields.Integer('Decimals Max')
    type = fields.Selection([('digits', 'digits'),('float','float'),('alpha','alpha'),('alphanum', 'alphanum')], required=True)
    display_name = fields.Char(compute='_compute_display_name')

    @api.multi
    def _compute_display_name(self):
        for record in self:
            record.display_name = "["+record.type+"] min: " + str(record.min)+ "  max: " + str(record.max)

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, record.display_name))
        return res

