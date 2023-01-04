# -*- coding: utf-8 -*-
"""License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)."""

from odoo import api, models


class WizardValueReport(models.AbstractModel):
    """pass value to template"""
    _name = "report.metro_barcode_print_community.print_product_labels"

    @api.model
    def _get_report_values(self, docids, data=None):
        same_page = self.env['ir.config_parameter'].sudo().get_param(
            'metro_barcode_print_community.same_page')
        separate_pages = self.env['ir.config_parameter'].sudo().get_param(
            'metro_barcode_print_community.separate_pages')
        product_ids = [index['product_id'] for index in data['product_label_moves']]
        move_line_ids = [index['move_line_id'] for index in data['product_label_moves']]
        product_template = self.env['product.product'].search([(
            'id', 'in', product_ids)])
        picking_id = self.env['stock.picking'].search([(
            'id', '=', data['product_label_moves'][0]['pic_id'])])
        print_copy = {}
        move_lines = picking_id.move_line_ids.filtered(lambda ml: ml.id in move_line_ids)
        for move_line in move_lines:
            print_copy.update({
                move_line.id: [i for i in range(0, int(move_line.qty_done))]
            })

        return {
            'doc_model': 'lot.barcode.report',
            'docs': product_template,
            'data': data,
            'same_page': same_page,
            'separate_page': separate_pages,
            'pick': picking_id,
            'move': move_lines,
            'print_copy': print_copy,
        }
