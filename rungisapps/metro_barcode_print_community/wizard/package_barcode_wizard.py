# -*- coding: utf-8 -*-

from odoo import models, fields


class PackageBarcodeLine(models.TransientModel):
    _name = "package.barcode.line"
    _description = 'Package Barcode Line'

    result_package_id = fields.Many2one('stock.quant.package',
                                        string='Package')
    print_copy = fields.Integer(string='Copies')
    wizard_id = fields.Many2one('package.barcode.report', string="Wizard")


class PackageBarcodeReport(models.TransientModel):
    _name = "package.barcode.report"
    _description = 'Package Barcode Report'

    package_moves = fields.One2many('package.barcode.line', 'wizard_id')

    def print_packages(self):
        package_move = []
        for moves in self.package_moves:
            data = {'result_package_id': moves.result_package_id.id,
                    'print_copy': moves.print_copy}
            package_move.append(data)
        dict1 = {'package_moves': package_move}
        return self.env.ref(
            'metro_barcode_print_community.action_print_package').report_action(self,
                                                                      data=dict1)

    def get_package_data(self, fields):
        if fields.get('active_id', False):
            picking_id = self.env['stock.picking'].browse(int(fields[
                                                                  'active_id']))
            result = [(0, 0, {'result_package_id': int(i)}) for i in
                      picking_id.move_line_ids.mapped('result_package_id')]
            return result
