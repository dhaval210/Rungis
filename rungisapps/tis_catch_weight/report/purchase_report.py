# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, fields, models, tools


class PurchaseReport(models.Model):
    _inherit = "purchase.report"
    _description = "Purchases Orders"
    _auto = False

    unit_cw_quantity = fields.Float(string='Product CW Quantity', readonly=True)
    product_cw_uom = fields.Many2one('uom.uom', string='Reference CW Unit of Measure', required=True)

    def _select(self):
        select_str = """
                WITH currency_rate as (%s)
                    SELECT
                        min(l.id) as id,
                        s.date_order as date_order,
                        s.state,
                        s.date_approve,
                        s.dest_address_id,
                        s.partner_id as partner_id,
                        s.user_id as user_id,
                        s.company_id as company_id,
                        s.fiscal_position_id as fiscal_position_id,
                        l.product_id,
                        p.product_tmpl_id,
                        t.categ_id as category_id,
                        s.currency_id,
                        t.uom_id as product_uom,
                        t.cw_uom_id as product_cw_uom,
                        sum(l.product_qty/u.factor*u2.factor) as unit_quantity,
                        sum(l.product_cw_uom_qty/cw_u.factor*cw_u2.factor) as unit_cw_quantity,
                        extract(epoch from age(s.date_approve,s.date_order))/(24*60*60)::decimal(16,2) as delay,
                        extract(epoch from age(l.date_planned,s.date_order))/(24*60*60)::decimal(16,2) as delay_pass,
                        count(*) as nbr_lines,
                        CASE WHEN t.catch_weight_ok = TRUE AND t.purchase_price_base = 'cwuom'
                        THEN sum(l.price_unit / COALESCE(cr.rate, 1.0) * l.product_cw_uom_qty)::decimal(16,2)
                        ELSE sum(l.price_unit / COALESCE(cr.rate, 1.0) * l.product_qty)::decimal(16,2)END as price_total,
                        CASE WHEN t.catch_weight_ok = TRUE AND t.purchase_price_base = 'cwuom'
                        THEN avg(100.0 * (l.price_unit / COALESCE(cr.rate,1.0) * l.product_cw_uom_qty) / NULLIF(ip.value_float*l.product_qty/u.factor*u2.factor, 0.0))::decimal(16,2)
                        ELSE avg(100.0 * (l.price_unit / COALESCE(cr.rate,1.0) * l.product_qty) / NULLIF(ip.value_float*l.product_qty/u.factor*u2.factor, 0.0))::decimal(16,2)END as negociation,
                        CASE WHEN t.catch_weight_ok = TRUE AND t.purchase_price_base = 'cwuom'
                        THEN sum(ip.value_float*l.product_cw_uom_qty/u.factor*u2.factor)::decimal(16,2)
                        ELSE sum(ip.value_float*l.product_qty/u.factor*u2.factor)::decimal(16,2)END as price_standard,
                        CASE WHEN t.catch_weight_ok = TRUE AND t.purchase_price_base = 'cwuom'
                        THEN (sum(l.product_cw_uom_qty * l.price_unit / COALESCE(cr.rate, 1.0))/NULLIF(sum(l.product_cw_uom_qty/cw_u.factor*cw_u2.factor),0.0))::decimal(16,2)
                        ELSE (sum(l.product_qty * l.price_unit / COALESCE(cr.rate, 1.0))/NULLIF(sum(l.product_qty/u.factor*u2.factor),0.0))::decimal(16,2)END as price_average, 
                        partner.country_id as country_id,
                        partner.commercial_partner_id as commercial_partner_id,
                        analytic_account.id as account_analytic_id,
                        sum(p.weight * l.product_qty/u.factor*u2.factor) as weight,
                        sum(p.volume * l.product_qty/u.factor*u2.factor) as volume
            """ % self.env['res.currency']._select_companies_rates()
        return select_str

    def _from(self):
        from_str = """
                purchase_order_line l
                    join purchase_order s on (l.order_id=s.id)
                    join res_partner partner on s.partner_id = partner.id
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                            LEFT JOIN ir_property ip ON (ip.name='standard_price' AND ip.res_id=CONCAT('product.product,',p.id) AND ip.company_id=s.company_id)
                    left join uom_uom u on (u.id=l.product_uom)
                    left join uom_uom cw_u on (cw_u.id=l.product_cw_uom)
                    left join uom_uom u2 on (u2.id=t.uom_id)
                    left join uom_uom cw_u2 on (cw_u2.id=t.cw_uom_id)
                    left join account_analytic_account analytic_account on (l.account_analytic_id = analytic_account.id)
                    left join currency_rate cr on (cr.currency_id = s.currency_id and
                        cr.company_id = s.company_id and
                        cr.date_start <= coalesce(s.date_order, now()) and
                        (cr.date_end is null or cr.date_end > coalesce(s.date_order, now())))
            """
        return from_str

    def _group_by(self):
        group_by_str = """
                GROUP BY
                    s.company_id,
                    s.user_id,
                    s.partner_id,
                    u.factor,
                    s.currency_id,
                    l.price_unit,
                    s.date_approve,
                    l.date_planned,
                    l.product_uom,
                    s.dest_address_id,
                    s.fiscal_position_id,
                    l.product_id,
                    p.product_tmpl_id,
                    t.categ_id,
                    s.date_order,
                    s.state,
                    u.uom_type,
                    u.category_id,
                    t.uom_id,
                    t.cw_uom_id,
                    u.id,
                    u2.factor,
                    partner.country_id,
                    partner.commercial_partner_id,
                    analytic_account.id,
                    t.catch_weight_ok,
                    t.purchase_price_base

            """
        return group_by_str
