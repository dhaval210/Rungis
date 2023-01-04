# -*- coding: utf-8 -*-
"""License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)."""

from odoo import api, models


class WizardValueReport(models.AbstractModel):
    """pass value to template"""
    _name = "report.metro_barcode_print_community.picking_print_packages"

    @api.model
    def _get_report_values(self, docids, data=None):
        same_page = self.env['ir.config_parameter'].sudo().get_param(
            'metro_barcode_print_community.same_page')
        separate_pages = self.env['ir.config_parameter'].sudo().get_param(
            'metro_barcode_print_community.separate_pages')
        package_ids = [index['result_package_id'] for index in data[
            'package_moves']]
        for package_moves in data['package_moves']:
            package_moves['print_copy'] = [i for i in range(0, int(
                package_moves['print_copy']))]
        stock_package_id = self.env['stock.quant.package'].search([(
            'id', '=', package_ids)])
        return {
            'doc_model': 'package.barcode.report',
            'docs': stock_package_id,
            'data': data,
            'same_page': same_page,
            'separate_page': separate_pages,
        }
