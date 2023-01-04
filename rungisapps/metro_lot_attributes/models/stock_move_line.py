from itertools import product
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MoveLine(models.Model):
    _inherit = 'stock.move.line'

    lot_attribute_line_ids = fields.One2many(
        comodel_name='stock.lot.attribute.lines',
        inverse_name='line_id',
        string='Attributes',
    )

    picking_type_create_lot_attributes = fields.Boolean(
        related="picking_id.picking_type_id.create_lot_attributes"
    )

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.id > 0:
            ids = []
            if res.product_id.id is not False:
                for attr_line in res.product_id.product_tmpl_id.attribute_line_ids.filtered(lambda avi: avi.lot_extension == True):
                    data = {
                        'line_id': res.id,
                        'attribute_id': attr_line.attribute_id.id,
                        'mandatory': attr_line.mandatory,
                        'product_tmpl_id': res.product_id.product_tmpl_id.id,
                    }
                    if self.lot_attribute_line_ids:
                        ext_line = self.lot_attribute_line_ids.filtered(lambda savi: savi.attribute_id == attr_line.attribute_id)
                        if len(ext_line) == 1:
                            data.update({
                                'value_ids': ext_line.value_ids.id
                            })
                            ext_line.value_ids = False
                    else:
                        lot_line = res.lot_id.lot_attribute_line_ids.filtered(lambda savi: savi.attribute_id == attr_line.attribute_id)
                        if lot_line:
                            data.update({
                                'value_ids': lot_line.value_ids.id if lot_line.value_ids else False
                            })
                    line = self.env['stock.lot.attribute.lines'].create(data)
                    ids += [line.id]
            if len(ids) > 0:
                res.lot_attribute_line_ids = [[6, 0, ids]]
        return res

    @api.multi
    def write(self, vals):
        error = []
        res = super().write(vals)
        for line in self:
            if (
                line.picking_id.picking_type_id.create_lot_attributes is True and
                'lot_attribute_line_ids' not in vals
            ):
                if len(line.lot_attribute_line_ids) > 0:
                    for attr_line in line.lot_attribute_line_ids:
                        if (
                            attr_line.mandatory is True and
                            attr_line.value_ids.id is False and
                            line.qty_done > 0
                        ):
                            error += ['Product: %s, Required value not set for %s' % (line.product_id.name, attr_line.attribute_id.name)]
                if (
                    len(line.lot_attribute_line_ids) > 0 and
                    line.lot_id.id > 0 and
                    len(line.lot_id.lot_attribute_line_ids) == 0
                ):
                    line.lot_id.write({
                        'lot_attribute_line_ids': [[6, 0, line.lot_attribute_line_ids.ids]]
                    })
        if len(error):
            raise ValidationError(
                '\n'.join(str(x) for x in error)
            )
        return res

    @api.multi
    def unlink(self):
        for line in self:
            if len(line.lot_attribute_line_ids) > 0:
                line.lot_attribute_line_ids.unlink()
        return super().unlink()
