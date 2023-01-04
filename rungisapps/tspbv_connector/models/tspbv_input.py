from odoo import api, fields, models


class Input(models.Model):
    _name = 'tspbv.input'
    _description = 'Input'

    grammar_rule_ids = fields.Many2many('tspbv.grammar.rule','input_grammar_rel','input_id', 'grammar_id','Grammar Rules')
    grammar_rules = fields.Char(string='Grammar rules', compute='get_grammar_rules')
    lydia_recognition_ids = fields.One2many(comodel_name='tspbv.recognition', inverse_name='input_id', string='Recognitions')
    lydia_scan_ids = fields.One2many(comodel_name='tspbv.scan', inverse_name='input_id',
                                            string='Scans')
    display_name = fields.Char(compute='_compute_display_name')

    @api.multi
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.grammar_rules

    @api.multi
    def get_grammar_rules(self):
        for record in self:
            grammar_rules = [x.rule_name for x in record.grammar_rule_ids]
            if grammar_rules:
                record.grammar_rules = ",".join(grammar_rules)

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, record.display_name))
        return res

