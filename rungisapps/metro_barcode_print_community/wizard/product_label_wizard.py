# -*- coding: utf-8 -*-

from odoo import models, fields


class ProductLabelsLine(models.TransientModel):
    _name = "product.label.line"
    _description = 'Product Label Line'

    move_line_id = fields.Integer(
        string="Move Line",
        required=True,
    )
    product_id = fields.Many2one('product.product', string="Product",
                                 required=True,
                                 domain="[('id', '=', product_id)]")
    pic_id = fields.Integer(string='Pick id')
    print_copy = fields.Integer(string='Copies')
    wizard_id = fields.Many2one('product.label.report', string="Wizard")


class ProductLabelsReport(models.TransientModel):
    _name = "product.label.report"
    _description = 'Product Label Report'

    product_label_moves = fields.One2many('product.label.line', 'wizard_id')

    def print_product_label(self):
        move_datas = []
        for moves in self.product_label_moves:
            data = {
                'move_line_id': moves.move_line_id,
                'product_id': moves.product_id.id,
                'print_copy': moves.print_copy,
                'pic_id': moves.pic_id
            }
            move_datas.append(data)
        dict1 = {'product_label_moves': move_datas}
        action = self.env.ref(
            'metro_barcode_print_community.action_print_product_labels').report_action(
            self, data=dict1)
        action.update({'close_on_report_download': True})
        return action

    def get_product_label(self, fields):
        if fields.get('active_id', False):
            picking_id = self.env['stock.picking'].browse(int(fields[
                                                                  'active_id']))
            result = [(0, 0, {'product_id': int(i)}) for i in
                      picking_id.move_line_ids.mapped('product_id')]
            return result
