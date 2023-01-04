from odoo import api, fields, models


class AppPicking(models.Model):
    _inherit = 'mobile.app.picking'

    @api.model
    def _export_move_line(self, line, custom_fields):
        res = super()._export_move_line(line, custom_fields)
        res.update({'pack_number': line.pack_number})
        return res

    @api.model
    def get_line_params(self, params):
        res = super().get_line_params(params)
        pack = self._extract_param(params, 'pack_number', '0')
        res.update({
            'pack_number': pack,
        })
        if pack != '0' and 'result_package_id' in res:
            del res['result_package_id']
        return res
