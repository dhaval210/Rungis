from odoo import api, fields, models


class BatchPicling(models.Model):
    _inherit = 'stock.picking.batch'

    tl_numbers = fields.Char(compute='_compute_label_numbers')

    @api.depends('picking_ids')
    def _compute_label_numbers(self):
        for rec in self:
            tl_number = []
            for pid in rec.picking_ids:
                tl_number += [pid.name[-3:]]
            rec.tl_numbers = ', '.join(tl_number)
            print(rec)
