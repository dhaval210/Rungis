# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import api, models, _, fields
from odoo.exceptions import UserError


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _make_po_get_domain(self, values, partner):
        domain = super(StockRule, self)._make_po_get_domain(values, partner)
        so_id = self.env['sale.order.line'].browse(values.get('sale_line_id'))
        po = self.env['purchase.order'].sudo().search([('origin', '=', so_id.order_id.name)])
        if not po:
            domain += (
                ('id', '=', '0'),
            )
        else:
            domain += (
                        ('id', 'in', tuple(po.ids)),
                    )
        return domain

    def _get_purchase_order_schedule_date(self, product_id, product_qty, product_uom, values, partner):
        today = fields.Datetime.now()
        seller = product_id.with_context(force_company=values['company_id'].id)._select_seller(
            partner_id=partner,
            quantity=product_qty,
            date=today and today.date(),
            uom_id=product_uom)

        return today + relativedelta(days=int(seller.delay))

    def _prepare_purchase_order(self, product_id, product_qty, product_uom, origin, values, partner):
        res = super(StockRule, self)._prepare_purchase_order(product_id, product_qty, product_uom, origin, values, partner)
        schedule_date = self._get_purchase_order_schedule_date(product_id, product_qty, product_uom, values, partner)
        purchase_date = fields.Datetime.now()
        res.update({
            'po_date_planned': schedule_date,
            'date_order': purchase_date
        })
        return res
