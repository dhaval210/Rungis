# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class BatchPicking(models.Model):
    _inherit = 'stock.picking.batch'

    @api.depends('picking_ids')
    def _compute_move_line_ids(self):
        move_line_ids = self.env['stock.move.line'].search(
            [('picking_id', 'in', self.picking_ids.ids)]
        )
        self.move_line_ids = move_line_ids.ids
        return True

    move_line_ids = fields.One2many(
        comodel_name='stock.move.line',
        inverse_name='batch_id',
        compute=_compute_move_line_ids
    )

    @api.multi
    def print_warehouse4(self):
        return self.env.ref('metro_rungis_report.warehouse4').report_action(
            self.id
        )

    @api.multi
    def print_transport_label(self):
        pickings = self.mapped('picking_ids')
        if not pickings:
            raise UserError(_('Nothing to print.'))
        return self.env.ref('metro_rungis_report.label').report_action(
            pickings.ids
        )

    @api.multi
    def print_transport_label_two(self):
        pickings = self.mapped('picking_ids')
        if not pickings:
            raise UserError(_('Nothing to print.'))
        return self.env.ref('metro_rungis_report.label2').report_action(
            pickings.ids
        )

    @api.multi
    def print_single_pickings(self):
        pickings = self.mapped('picking_ids')
        if not pickings:
            raise UserError(_('Nothing to print.'))
        return self.env.ref('stock.action_report_picking').report_action(
            pickings.ids
        )


class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    sorted_location = fields.Integer(related="location_id.sort",
                                     string='Sorting', store=True)
