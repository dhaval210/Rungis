from odoo import api, fields, models


class AppPicking(models.Model):
    _inherit = 'mobile.app.picking'

    @api.model
    def _export_move_line(self, line, custom_fields):
        res = super()._export_move_line(line, custom_fields)
        if (
            len(line.lot_attribute_line_ids) and
            line.picking_type_create_lot_attributes is True
        ):
            generic = []
            for lali in line.lot_attribute_line_ids:
                valid_values = []
                if len(lali.valid_product_attribute_value_ids):
                    valid_vals = lali.valid_product_attribute_value_ids
                    for valid in valid_vals.filtered(lambda x: x.attribute_id == lali.attribute_id):
                        valid_values += [{
                            'id': valid.id,
                            'label': valid.name,
                            'selected': True if lali.value_ids.id == valid.id else False
                        }]
                generic += [{
                    'attribute_line_id': lali.id,
                    'attribute_id': lali.attribute_id.id,
                    'attribute_label': lali.attribute_id.name,
                    'mandatory': lali.mandatory,
                    'valid_values': valid_values
                }]
            if len(generic):
                res.update({
                    'generic_attributes': generic,
                })
        return res

    @api.model
    def get_line_params(self, params):
        res = super().get_line_params(params)
        StockMoveLine = self.env['stock.move.line']
        move_line_id = self._extract_param(params, 'move.id')
        move_line = StockMoveLine.search([('id', '=', move_line_id)])
        if (move_line.lot_attribute_line_ids):
            lines_values = []
            for lid in move_line.lot_attribute_line_ids.ids:
                line_val = self._extract_param(
                    params,
                    'move.generic.line_.' + str(lid),
                    False
                )
                if line_val:
                    lines_values += [(1, lid, {'value_ids': line_val})]
            if len(lines_values):
                res.update({
                    'lot_attribute_line_ids': lines_values,
                })
        return res
