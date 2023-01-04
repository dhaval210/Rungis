# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import timedelta, datetime, date
import pytz
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    calling_time = fields.Float('Gewünschte Anrufszeit', related='partner_id.calling_time')
    calling_date = fields.Datetime(string='Anrufsplan')
    tour_default_departure = fields.Float('Default Departure', related='tour_id.tour_default_departure')

    #sequence field instead of drop-off because reordering only possible with sequence in kanban view
    sequence = fields.Integer('Sequence', default=1)

    original_user_id = fields.Many2one('res.users', string='Vertretung von', compute='_compute_original_user_id')
    weight = fields.Float(compute='_cal_so_weight_volume', store=True)
    volume = fields.Float(compute='_cal_so_weight_volume', store=True)

    @api.depends('order_line')
    def _cal_so_weight_volume(self):
        for so in self:
            weight = 0
            volume= 0
            for sol in so.order_line:
                weight += sol.product_id.weight * sol.product_uom_qty
                volume += sol.product_id.volume * sol.product_uom_qty
            so.weight = weight
            so.volume = volume


    @api.depends('user_id','partner_id')
    def _compute_original_user_id(self):
        for so in self:
            if so.user_id != so.partner_id.user_id:
                so.original_user_id = so.partner_id.user_id.id
            else:
                so.original_user_id = False

    @api.onchange('commitment_date')
    def _onchange_commitment_date_tour(self):
        ret = super(SaleOrder, self).onchange_sale_order_template_id()
        if self.commitment_date:
            assignment_id = self.env['tour.assignment'].search([
                ('partner_id','=',self.partner_id.id),
                ('order_deadline', '=', self.commitment_date.weekday())])
            if assignment_id:
                self.tour_id = assignment_id.tour_id.id
                return ret
            else:
                return {
                    'warning': {
                        'title': _('Keine Tour definiert.'),
                        'message': _("Für diesen Wochentag ist für diesen Kunden keine Tour definiert, bitte ein anderes Datum wählen.")
                    }
                }
