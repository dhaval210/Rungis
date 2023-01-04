from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Lot(models.Model):
    _inherit = 'stock.production.lot'

    lot_attribute_line_ids = fields.One2many(
        comodel_name='stock.lot.attribute.lines',
        inverse_name='lot_id',
        string='Attributes',
    )

    def generate_attribute_lines(self):
        if not self.id > 0:
            self.create()
        if self.id > 0:
            ids = []
            if self.product_id.id is not False:
                for attr_line in self.product_id.product_tmpl_id.attribute_line_ids.filtered(lambda avi: avi.lot_extension == True):
                    line = self.env['stock.lot.attribute.lines'].create({
                        'lot_id': self.id,
                        'attribute_id': attr_line.attribute_id.id,
                        'mandatory': attr_line.mandatory,
                        'product_tmpl_id': self.product_id.product_tmpl_id.id,
                    })
                    ids += [line.id]
            if len(ids) > 0:
                self.write({
                    'lot_attribute_line_ids': [[6, 0, ids]]
                })
