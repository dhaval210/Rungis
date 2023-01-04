# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import timedelta, datetime, date
import pytz
from odoo.exceptions import UserError

class HrLeave(models.Model):
    _inherit = "hr.leave"

    sale_order_reassign_count = fields.Integer(compute='_compute_sale_order_reassign_count', string='Sale Order Reassign Count')

    def _compute_sale_order_reassign_count(self):
        partner_ids = self.env['res.partner'].search(['|',
            ('user_id','=',self.employee_id.user_id.id),
            ('substitute_user_id', '=', self.employee_id.user_id.id),
            ])
        if partner_ids:
            self.sale_order_reassign_count = self.env['sale.order'].search_count([
                ('user_id', '!=', self.employee_id.user_id.id),
                ('partner_id','in',partner_ids.ids),
                ('calling_date','>=',self.request_date_from),
                ('calling_date','<',self.request_date_to+timedelta(days=1)),
            ])

    def action_view_reassign_so(self):
        self.ensure_one()
        action = self.env.ref('metro_sales_tour.calling_plan_substitute').read()[0]
        partner_ids = self.env['res.partner'].search(['|',
            ('user_id','=',self.employee_id.user_id.id),
            ('substitute_user_id', '=', self.employee_id.user_id.id),
            ])
        if partner_ids:
            sale_order_reassign_ids = self.env['sale.order'].search([
                ('partner_id','in',partner_ids.ids),
                ('calling_date','>=',self.request_date_from),
                ('calling_date','<',self.request_date_to+timedelta(days=1)),
            ])

            if sale_order_reassign_ids:
                action['domain'] = [('id', 'in', sale_order_reassign_ids.ids)]
                return action


    @api.multi
    def action_reassign(self):
        if any(holiday.state not in ['validate'] for holiday in self):
            raise UserError(_('Leave request state must be "Refused" or "To Approve" in order to be reassigned'))
        for holiday in self:
            reassign_so_ids = self.env['sale.order'].search([
                ('calling_date','>=',holiday.request_date_from),
                ('calling_date','<',holiday.request_date_to+timedelta(days=1)),
                ('user_id','=',holiday.employee_id.user_id.id),
                ])
            for so in reassign_so_ids:
                substitute_emp_id = so.partner_id.substitute_user_id.employee_ids
                if substitute_emp_id:
                    substitute_leave = self.search([
                            ('employee_id', '=', substitute_emp_id[0].id),
                            ('date_from', '<=', so.calling_date.date()),
                            ('date_to', '>=', so.calling_date.date()),
                            ('state', '=', 'validate')
                        ])
                    if substitute_leave:
                        so.write({'user_id':False})
                    else:
                        so.write({'user_id':so.partner_id.substitute_user_id.id})
                else:
                    so.write({'user_id':False})
        return True

    @api.multi
    def action_reassign_cancel(self):
        for holiday in self:
            partner_ids = self.env['res.partner'].search(['|',
              ('user_id', '=', self.employee_id.user_id.id),
              ('substitute_user_id', '=', self.employee_id.user_id.id),
              ])
            if partner_ids:
                sale_order_reassign_ids = self.env['sale.order'].search([
                    ('partner_id', 'in', partner_ids.ids),
                    ('calling_date', '>=', self.request_date_from),
                    ('calling_date', '<', self.request_date_to + timedelta(days=1)),
                ])
                for so in sale_order_reassign_ids:
                    so.write({'user_id':self.employee_id.user_id.id})

        return True