# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def action_confirm(self):
        result = super(SaleOrder, self).action_confirm()
        for order in self:
            rate = self.env['res.currency']._get_conversion_rate(
                order.currency_id, order.company_id.currency_id,
                order.company_id, order.date_order)
            total_currency = order.amount_untaxed * rate
            employee_id = self.env['hr.employee'].search([('address_id', 'in', [order.partner_id.id, order.partner_id.parent_id.id])], limit=1)
            if employee_id:
                limit = employee_id.min_amount_employee
                if total_currency < limit:
                    raise UserError(
                        _('The total amount %s is below the %s limit for this employee.')
                        % (formatLang(self.env, total_currency or 0.0, currency_obj=order.company_id.currency_id, monetary=True),
                           formatLang(self.env, limit or 0.0, currency_obj=order.company_id.currency_id, monetary=True)))
            elif order.partner_id.kac and order.company_id.min_amount_kac_customer:
                limit = order.company_id.min_amount_kac_customer
                if total_currency < limit:
                    raise UserError(
                        _('The total amount %s is below the %s limit for this customer type (KAC).')
                        % (formatLang(self.env, total_currency or 0.0, currency_obj=order.company_id.currency_id, monetary=True),
                           formatLang(self.env, order.company_id.min_amount_kac_customer or 0.0, currency_obj=order.company_id.currency_id, monetary=True)))
            elif not order.partner_id.kac and order.company_id.min_amount_customer:
                limit = order.company_id.min_amount_customer
                if total_currency < limit:
                    raise UserError(
                        _('The total amount %s is below the %s limit for this customer type (non KAC).')
                        % (formatLang(self.env, total_currency or 0.0, currency_obj=order.company_id.currency_id, monetary=True),
                           formatLang(self.env, order.company_id.min_amount_customer or 0.0, currency_obj=order.company_id.currency_id, monetary=True)))
        return result

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(SaleOrder, self).onchange_partner_id()
        if self.partner_id:
            employee_id = self.env['hr.employee'].search([('address_id', '=', self.partner_id.id)], limit=1)
            if employee_id:
                res = res or {'domain': {}}
                res['domain']['partner_shipping_id'] = [
                    ('id', 'in', [p.id for p in self.company_id.employee_delivery_address_ids])
                ]
                self.partner_shipping_id = False
                self.partner_invoice_id = self.partner_id
        return res
