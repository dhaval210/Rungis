# -*- coding: utf-8 -*-

from odoo import models, fields


class LotBarcodeLine(models.TransientModel):
    _name = "lot.barcode.line"
    _description = 'Lot Barcode Line'

    product_id = fields.Many2one('product.product', string="Product",
                                 required=True,
                                 domain="[('id', '=', product_id)]")
    lot_id = fields.Many2one('stock.production.lot', string='Lot',
                             required=True)
    print_copy = fields.Integer(string='Copies')
    use_date = fields.Datetime(string='Best Before Date')
    include_use_date = fields.Boolean('Best Before Date Include')
    wizard_id = fields.Many2one('lot.barcode.report', string="Wizard")


class LotBarcodeReport(models.TransientModel):
    _name = "lot.barcode.report"
    _description = 'Lot Barcode Report'

    product_moves = fields.One2many('lot.barcode.line', 'wizard_id')

    def print_lots(self):
        move_datas = []
        for moves in self.product_moves:
            data = {'product_id': moves.product_id.id,
                    'lot_id': moves.lot_id.id,
                    'print_copy': moves.print_copy,
                    'use_date': moves.use_date,
                    'include_use_date': moves.include_use_date}
            move_datas.append(data)
        dict1 = {'product_moves': move_datas}
        return self.env.ref(
            'metro_barcode_print_community.action_print_lots').report_action(self,
                                                                   data=dict1)

    def get_barcode_lot(self, fields):
        if fields.get('active_id', False):
            picking_id = self.env['stock.picking'].browse(int(fields[
                'active_id']))
            result = [(0, 0, {'product_id': int(product_id)}) for product_id in
                      picking_id.move_line_ids.mapped('product_id')]
            return result
