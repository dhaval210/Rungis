# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api


class AccountInvoiceReports(models.Model):
    _name = "account.invoice.reports"
    _inherit = 'account.invoice.report'
    _description = "Metro Invoices Report"
    _auto = False

    purchase_price = fields.Float(string='Cost', readonly=True)
    landed_costs = fields.Float(string="Landed Costs", readonly=True)
    margin = fields.Float(string="Margin (Gross)", readonly=True)
    margin_lc = fields.Float(string="Margin including LC", readonly=True)
    margin_percent = fields.Float(string="Margin inc. LC(%)", readonly=True)
    buying_potential = fields.Float('Yearly Buying potential', readonly=True)
    sales_target = fields.Float('Yearly Sales Target', readonly=True)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        # set buying_potential and sales_target value of partner
        # calculate  margin_percent based on margin_lc and price_total
        res = super(AccountInvoiceReports, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        for line in res:
            if 'margin_percent' in line and 'margin_lc' in line and 'price_total' in line:
                try:
                    line['margin_percent'] = line['margin_lc'] * 100 / line['price_total']
                except (ZeroDivisionError, TypeError) as e:
                    line['margin_percent'] = 0.0
            partners = self.search(line.get('__domain', [])).mapped('commercial_partner_id')
            buying_potential = sum(partners.mapped('buying_potential'))
            sales_target = sum(partners.mapped('sales_target'))
            if 'buying_potential' in line:
                line['buying_potential'] = buying_potential
            if 'sales_target' in line:
                line['sales_target'] = sales_target
        return res

    def _select(self):
        select_str = super(AccountInvoiceReports, self)._select() + """,
                                                                        sub.purchase_price as purchase_price,
                                                                        sub.landed_costs as landed_costs,
                                                                        sub.margin as margin,
                                                                        sub.margin_lc as margin_lc,
                                                                        sub.margin_percent as margin_percent,
                                                                        rp.buying_potential as buying_potential,
                                                                        rp.sales_target as sales_target
                                                                    """
        return select_str

    def _sub_select(self):
        sub_select = super(AccountInvoiceReports, self)._sub_select() + """,
                                                                            SUM(ail.purchase_price * ail.quantity) as purchase_price,
                                                                            SUM(ail.landed_costs * ail.quantity) as landed_costs,
                                                                            SUM(ail.margin) as margin,
                                                                            SUM(ail.margin_lc) as margin_lc,
                                                                            SUM(ail.margin_percent) as margin_percent
                                                                        """
        return sub_select

    def _from(self):
        return super(AccountInvoiceReports, self)._from()

    def _group_by(self):
        return super(AccountInvoiceReports, self)._group_by()

    @api.model_cr
    def init(self):
        # self._table = account_invoice_reports
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            WITH currency_rate AS (%s)
            %s
            FROM (
                %s %s %s
            ) AS sub
            LEFT JOIN currency_rate cr ON
                (cr.currency_id = sub.currency_id AND
                 cr.company_id = sub.company_id AND
                 cr.date_start <= COALESCE(sub.date, NOW()) AND
                 (cr.date_end IS NULL OR cr.date_end > COALESCE(sub.date, NOW())))
            LEFT JOIN res_partner rp ON rp.id = sub.partner_id
        )""" % (
                    self._table, self.env['res.currency']._select_companies_rates(),
                    self._select(), self._sub_select(), self._from(), self._group_by()))
