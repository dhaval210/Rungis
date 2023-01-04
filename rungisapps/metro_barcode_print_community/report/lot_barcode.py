# -*- coding: utf-8 -*-
"""License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)."""

from odoo import api, models


class WizardValueReport(models.AbstractModel):
    """pass value to template"""
    _name = "report.metro_barcode_print_community.pick_print_lots"

    @api.model
    def _get_report_values(self, docids, data=None):
        lot_ids = [index['lot_id'] for index in data['product_moves']]
        for product_moves in data['product_moves']:
            product_moves['print_copy'] = [i for i in range(0, int(
                product_moves['print_copy']))]
        stock_production_lot_id = self.env['stock.production.lot'].search([(
            'id', 'in', lot_ids)])
        same_page = self.env['ir.config_parameter'].sudo().get_param(
            'metro_barcode_print_community.same_page')
        separate_pages = self.env['ir.config_parameter'].sudo().get_param(
            'metro_barcode_print_community.separate_pages')
        return {
            'doc_model': 'lot.barcode.report',
            'docs': stock_production_lot_id,
            'data': data,
            'same_page': same_page,
            'separate_page': separate_pages,
        }
