from odoo import api, fields, models


class MoveLine(models.Model):
    _inherit = 'stock.move.line'

    piece_fish = fields.Boolean(string="Piece Fish", default=False, compute='_compute_piece_fish')

    @api.depends('product_id')
    def _compute_piece_fish(self):
        ref_categ = self.env['ir.config_parameter'].sudo().get_param('fish_product_category_name')
        for rec in self:
            for line in rec.product_id.categ_ids:
                if line.name == ref_categ:
                    rec.piece_fish = True
                else:
                    rec.piece_fish = False

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        print_on = self.env['ir.config_parameter'].sudo().get_param(
            'metro_barcode_print_community.print_on')
        if print_on == 'line' and 'qty_done' in vals:
            for line in self:
                type = line.picking_id.picking_type_id
                if type.allow_print:
                    line.picking_id.call_pdf_report([line.id], False)
        return res
