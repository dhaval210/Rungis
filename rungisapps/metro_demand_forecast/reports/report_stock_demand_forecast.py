# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class ReportStockForecat(models.Model):
    _name = 'report.stock.demand.forecast'
    _auto = False
    _description = 'Stock Demand Forecast Report'

    date = fields.Date(string='Date')
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', string='Product Template', related='product_id.product_tmpl_id', readonly=True)
    cumulative_quantity = fields.Float(string='Cumulative Quantity', readonly=True)
    quantity = fields.Float(readonly=True)
    outgoing_quantity = fields.Float(readonly=True)
    incoming_quantity = fields.Float(readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_stock_demand_forecast')
        self._cr.execute("""CREATE or REPLACE VIEW report_stock_demand_forecast AS (SELECT
        MIN(id) as id,
        product_id as product_id,
        to_char(date, 'YYYY-MM-DD') as date,
        sum(product_qty) AS quantity,
        sum(outgoing_qty) AS outgoing_quantity,
        sum(incoming_qty) AS incoming_quantity,
        sum(sum(product_qty) - sum(outgoing_qty) + sum(incoming_qty)) OVER (PARTITION BY product_id, company_id ORDER BY date) AS cumulative_quantity,
        company_id
        FROM
        (
        SELECT
        MIN(id) as id,
        MAIN.product_id as product_id,
        SUB.date as date,
        CASE WHEN MAIN.date = SUB.date THEN sum(MAIN.product_qty) ELSE 0 END as product_qty,
        CASE WHEN MAIN.date = SUB.date THEN sum(MAIN.outgoing_qty) ELSE 0 END as outgoing_qty,
        CASE WHEN MAIN.date = SUB.date THEN sum(MAIN.incoming_qty) ELSE 0 END as incoming_qty,
        MAIN.company_id as company_id
        FROM
        (
            SELECT
            MIN(sq.id) as id,
            sq.product_id,
            date_trunc('day', to_date(to_char(CURRENT_DATE, 'YYYY/MM/DD'), 'YYYY/MM/DD')) as date,
            SUM(sq.quantity) AS product_qty,
            SUM(0) as outgoing_qty,
            SUM(0) as incoming_qty,
            sq.company_id
            FROM
            stock_quant as sq
            LEFT JOIN
            product_product ON product_product.id = sq.product_id
            LEFT JOIN
            stock_location location_id ON sq.location_id = location_id.id
            WHERE
            location_id.usage = 'internal'
            GROUP BY date, sq.product_id, sq.company_id

            UNION ALL
            SELECT
            MIN(-pol.id) as id,
            pol.product_id,
            CASE WHEN pol.date_planned > CURRENT_DATE
            THEN date_trunc('day', to_date(to_char(pol.date_planned, 'YYYY/MM/DD'), 'YYYY/MM/DD'))
            ELSE date_trunc('day', to_date(to_char(CURRENT_DATE, 'YYYY/MM/DD'), 'YYYY/MM/DD')) END
            AS date,
            SUM(0) AS product_qty,
            SUM(0) as outgoing_qty,
            SUM(pol.product_qty - COALESCE(pol.qty_received, 0)) AS incoming_qty,
            pol.company_id
            FROM
                purchase_order_line as pol
            LEFT JOIN
                product_product ON product_product.id = pol.product_id
            LEFT JOIN
                purchase_order ON pol.order_id = purchase_order.id              
            WHERE
            purchase_order.state IN ('draft', 'sent', 'to approve', 'purchase') and
            pol.date_planned >= CURRENT_DATE
            GROUP BY pol.date_planned,pol.product_id, pol.company_id
            UNION ALL

            SELECT
                MIN(-sol.id) as id,
                sol.product_id,
                CASE WHEN sale_order.commitment_date >= CURRENT_DATE
                    THEN date_trunc('day', to_date(to_char(sale_order.commitment_date, 'YYYY/MM/DD'), 'YYYY/MM/DD') - integer '1')
                    ELSE date_trunc('day', to_date(to_char(CURRENT_DATE, 'YYYY/MM/DD'), 'YYYY/MM/DD') - integer '1') END
                AS date,
                SUM(0) AS product_qty,
                CASE WHEN SUM(sol.demand_qty) > 0
                    THEN SUM(sol.demand_qty - sol.qty_delivered)
                    ELSE SUM(sol.product_uom_qty - sol.qty_delivered) END
                as outgoing_qty,
                SUM(0) AS incoming_qty,
                sol.company_id
            FROM
                sale_order_line as sol
            LEFT JOIN
                product_product ON product_product.id = sol.product_id
            LEFT JOIN
                sale_order ON sol.order_id = sale_order.id
            WHERE
                sale_order.state IN ('draft', 'sent', 'sale') AND sale_order.commitment_date >= CURRENT_DATE
            GROUP BY sale_order.commitment_date,sol.product_id,sol.company_id
        )     
        as MAIN
    LEFT JOIN
    (
        SELECT DISTINCT date
    FROM
        (
            SELECT date_trunc('day', CURRENT_DATE) AS DATE
            UNION ALL
            SELECT date_trunc('day', to_date(to_char(sale_order.commitment_date, 'YYYY/MM/DD'), 'YYYY/MM/DD') - integer '1') AS date
            FROM sale_order_line sol
            LEFT JOIN
                sale_order ON sol.order_id = sale_order.id            
            WHERE
            sol.state IN ('draft', 'sent', 'sale') and sale_order.commitment_date > CURRENT_DATE + integer '1'
            UNION ALL
            SELECT date_trunc('day', to_date(to_char(pol.date_planned, 'YYYY/MM/DD'), 'YYYY/MM/DD')) AS date
            FROM purchase_order_line pol
            WHERE
                pol.state IN ('draft', 'sent', 'to approve', 'purchase') and
                pol.date_planned >= CURRENT_DATE
        ) AS DATE_SEARCH)
        SUB ON (SUB.date IS NOT NULL)    
    GROUP BY MAIN.product_id,SUB.date, MAIN.date, MAIN.company_id
    ) AS FINAL
    WHERE product_qty > 0 or outgoing_qty > 0 or incoming_qty > 0
    GROUP BY product_id,date,company_id)""")
