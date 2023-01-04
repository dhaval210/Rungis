from odoo import models, fields, api
import ast


class ResConfigSettings(models.TransientModel):
    """inherit inventory config and add two booleans"""
    _inherit = 'res.config.settings'

    generic_label_ids = fields.Many2many(comodel_name='res.generic.label')
    

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        label_ids = get_param('metro_barcode_print_community_generic_label_filter.generic_label_ids')
        if label_ids is False or label_ids == 'res.generic.label()':
            label_ids = [(6, 0, [])]
        else:
            label_ids = [(6, 0, ast.literal_eval(label_ids))]
        res.update(
            generic_label_ids=label_ids,
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()

        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param(
            "metro_barcode_print_community_generic_label_filter.generic_label_ids",
            self.generic_label_ids.ids
        )
