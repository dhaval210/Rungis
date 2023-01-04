# -*- coding: utf-8 -*-
"""License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)."""

import base64
from io import BytesIO

import qrcode

from odoo import models, fields, api


class Picking(models.Model):
    """inherit stock picking for report"""
    _inherit = "stock.picking"

    contain_piece_fish = fields.Boolean(string="Contains Piece Fish",
                                        compute='_compute_contain_piece_fish')

    @api.depends('move_line_ids_without_package.piece_fish')
    def _compute_contain_piece_fish(self):
        for rec in self.move_line_ids_without_package:
            if rec.piece_fish is True:
                self.contain_piece_fish = True
            else:
                self.contain_piece_fish = False

    def action_print_lots(self):
        """ while clicking  print lot  function used to pass value to
              wizard"""
        product_list = []
        for res in self.move_line_ids:
            product_list.append((0, 0, {'product_id': res.product_id.id,
                                        'use_date': res.use_date,
                                        'lot_id': res.lot_id.id}))
        return {
            'name': 'Print Lot',
            'type': 'ir.actions.act_window',
            'view_mode': 'form,tree',
            'res_model': 'lot.barcode.report',
            'target': 'new',
            'context': {
                'default_product_moves': product_list,
            },
        }

    def action_packages(self):
        """ while clicking  print packages function used to pass value to
        wizard"""

        package_list = []
        for move in self.move_line_ids:
            package_list.append(
                {'result_package_id': move.result_package_id.id})
        avoid_duplicates_package = [dict(t) for t in {tuple(d.items()) for d in
                                                      package_list}]
        return {
            'name': 'Print Packages',
            'type': 'ir.actions.act_window',
            'view_mode': 'form,tree',
            'res_model': 'package.barcode.report',
            'target': 'new',
            'context': {
                'default_package_moves': avoid_duplicates_package,
            },
        }

    def action_package_contents(self):
        """ while clicking print package contents,function used to pass
        value to wizard"""
        package_content_list = []
        for move in self.move_line_ids:
            package_content_list.append(
                {'result_package_id': move.result_package_id.id})
        avoid_duplicates_content = [dict(t) for t in {tuple(d.items()) for d in
                                                      package_content_list}]
        return {
            'name': 'Print Packages Barcode Content',
            'type': 'ir.actions.act_window',
            'view_mode': 'form,tree',
            'res_model': 'content.barcode.report',
            'target': 'new',
            'context': {
                'default_package_content_moves':
                    avoid_duplicates_content,
            },
        }

    def action_product_label(self):
        """ while clicking print product label,function used to pass
               value to wizard"""
        product_list = []
        for res in self.move_line_ids:
            product_list.append((
                0,
                0,
                {
                    'move_line_id': res.id,
                    'product_id': res.product_id.id,
                    'print_copy': res.qty_done,
                    'pic_id': self.id
                }
            ))
        return {
            'name': 'Print product labels',
            'type': 'ir.actions.act_window',
            'view_mode': 'form,tree',
            'res_model': 'product.label.report',
            'target': 'new',
            'context': {
                'default_product_label_moves': product_list,
            },
        }

    @api.multi
    def button_validate(self):
        current_user = self.env.user
        res = super(Picking, self).button_validate()
        print_on = self.env['ir.config_parameter'].sudo().get_param(
            'metro_barcode_print_community.print_on')
        if print_on == 'validate' and self.picking_type_id.allow_print:
            printing_ids = self._context.get('printing_ids')
            default_action = self._context.get('default_action')
            if (
                not res and
                current_user.printing_action != 'server' and
                len(printing_ids) == 0 and
                default_action != 'server'
            ):
                context = self._context.copy()
                if context.get('cw_params'):
                    del context['cw_params']
                self.env.context = context
                return self.call_pdf_report(self.move_line_ids.ids, True)
            elif not res:
                return
            else:
                return res
        if not res:
            return
        return res

    @api.multi
    def action_done(self):
        current_user = self.env.user
        res = super().action_done()
        print_on = self.env['ir.config_parameter'].sudo().get_param(
            'metro_barcode_print_community.print_on')
        if print_on == 'validate' and self.picking_type_id.allow_print:
            actions_report = self.env['ir.actions.report']
            report_id = actions_report.search([('report_name', '=', 'metro_barcode_print_community.print_product_labels')], limit=1)

            default_action = False
            if len(report_id) and len(report_id.property_printing_action_id):
                default_action = report_id.property_printing_action_id.action_type

            report_xml = self.env['printing.report.xml.action']
            printing_ids = report_xml.search([('user_id', '=', current_user.id), ('action', '=', 'server'), ('report_id', '=', report_id.id)])
            context = self._context.copy()
            context.update({
                'printing_ids': printing_ids,
                'default_action': default_action
            })
            self.env.context = context
            if (
                res is True and
                current_user.printing_action == 'server' or
                len(printing_ids) > 0 or
                default_action == 'server'
            ):
                self.call_pdf_report(self.move_line_ids.ids)
        return True

    def call_pdf_report(self, line_ids=[], pdf=False, report_id='metro_barcode_print_community.action_print_product_labels'):
        move_datas = []
        for res in self.move_line_ids.filtered(lambda r: r.id in line_ids):
            if res.qty_done > 0:
                data = {
                    'move_line_id': res.id,
                    'product_id': res.product_id.id,
                    'print_copy': res.qty_done,
                    'pic_id': self.id
                }
                move_datas.append(data)
        if len(move_datas) > 0:
            dict1 = {'product_label_moves': move_datas}
            if not pdf:
                self.env.ref(report_id).render_qweb_pdf(
                    res_ids=[self.id],
                    data=dict1
                )
                return True
            else:
                return self.env.ref(report_id).report_action(self, data=dict1)


class PickingType(models.Model):
    _inherit = "stock.picking.type"

    allow_print = fields.Boolean(string="Allow Print", help="check this  "
                                                            "option to print "
                                                            "label report")


class StockProductionLot(models.Model):
    """inherit stock picking for Generating Qr code for best before date """
    _inherit = "stock.production.lot"

    qr_code = fields.Binary("QR Code For Best Before Datesa", store=True)
    qr_code_lot = fields.Binary("QR Code For Lot", store=True)

    @api.constrains('use_date')
    def generate_qr_code(self):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.use_date)
        qr.make(fit=True)
        img = qr.make_image()
        temp = BytesIO()
        img.save(temp, format="PNG")
        qr_image = base64.b64encode(temp.getvalue())
        self.qr_code = qr_image

    @api.constrains('name')
    @api.onchange('name')
    def generate1_qr_code(self):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.name)
        qr.make(fit=True)
        img = qr.make_image()
        temp = BytesIO()
        img.save(temp, format="PNG")
        qr_image = base64.b64encode(temp.getvalue())
        self.qr_code_lot = qr_image
