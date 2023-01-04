from odoo import models, fields, api
import ast


class ResConfigSettings(models.TransientModel):
    """inherit inventory config and add two booleans"""
    _inherit = 'res.config.settings'

    piece_fish_operation_type_ids = fields.Many2many(comodel_name='stock.picking.type')
    

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        type_ids = get_param('metro_rungis_fish_label_report.piece_fish_operation_type_ids')
        if type_ids is False or type_ids == 'stock.picking.type()':
            type_ids = [(6, 0, [])]
        else:
            type_ids = [(6, 0, ast.literal_eval(type_ids))]
        res.update(
            piece_fish_operation_type_ids=type_ids,
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()

        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param(
            "metro_rungis_fish_label_report.piece_fish_operation_type_ids",
            self.piece_fish_operation_type_ids.ids
        )
