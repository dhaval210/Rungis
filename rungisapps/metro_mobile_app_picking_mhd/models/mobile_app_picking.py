from odoo import api, fields, models


class AppPicking(models.Model):
    _inherit = 'mobile.app.picking'

    @api.model
    def _export_move_line(self, line, custom_fields):
        res = super()._export_move_line(line, custom_fields)

        if line.lot_id.use_date is not False:
            pack_mhd = line.lot_id.use_date.date()
        else:
            pack_mhd = False

        res.update({
                'lot_mhd': line.lot_mhd,
                'pack_mhd': pack_mhd,
            })
        return res

    @api.model
    def get_line_params(self, params):
        res = super().get_line_params(params)
        mhd = self._extract_param(params, 'lot_mhd', 0)
        res.update({
            'lot_mhd': mhd,
        })
        return res
