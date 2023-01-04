from odoo import models, fields, api
import ast


class ResConfigSettings(models.TransientModel):
    """inherit inventory config and add two booleans"""
    _inherit = 'res.config.settings'

    res_generic_warehouse_ids = fields.Many2many(comodel_name='res.generic.warehouse')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        generic_warehouse_ids = get_param('metro_cache_order_grid_stock.res_generic_warehouse_ids')
        if generic_warehouse_ids is False or generic_warehouse_ids == 'res.generic.warehouse()':
            generic_warehouse_ids = [(6, 0, [])]
        else:
            generic_warehouse_ids = [(6, 0, ast.literal_eval(generic_warehouse_ids))]
        res.update(
            res_generic_warehouse_ids=generic_warehouse_ids,
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()

        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param(
            "metro_cache_order_grid_stock.res_generic_warehouse_ids",
            self.res_generic_warehouse_ids.ids
        )
