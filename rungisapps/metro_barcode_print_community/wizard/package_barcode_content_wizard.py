# -*- coding: utf-8 -*-

from odoo import models, fields


class ContentBarcodeLine(models.TransientModel):
    _name = "content.barcode.line"
    _description = 'Content Barcode Line'

    result_package_id = fields.Many2one('stock.quant.package', string='Package')
    print_copy = fields.Integer(string='Copies')
    wizard_id = fields.Many2one('content.barcode.report', string="Wizard")


class ContentBarcodeReport(models.TransientModel):
    _name = "content.barcode.report"
    _description = 'Content Barcode Report'

    package_content_moves = fields.One2many('content.barcode.line', 'wizard_id')

    def print_packages_content(self):
        move_content = []
        for moves in self.package_content_moves:
            data = {'result_package_id': moves.result_package_id.id,
                    'print_copy': moves.print_copy}
            move_content.append(data)
        dict1 = {'package_content_moves': move_content}
        return self.env.ref(
            'metro_barcode_print_community.action_print_package_content').report_action(self,
                                                                   data=dict1)

    def get_content_data(self, fields):
        if fields.get('active_id', False):
            picking_id = self.env['stock.picking'].browse(int(fields[
                                                                  'active_id']))
            result = [(0, 0, {'result_package_id': int(i)}) for i in
                      picking_id.move_line_ids.mapped('result_package_id')]
            return result