# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import tools
from odoo import models, fields, api


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"
    _auto = False

    product_cw_qty = fields.Float(string='Product CW Quantity', readonly=True)

    def _select(self):
        return super(AccountInvoiceReport, self)._select() + ", sub.product_cw_qty"

    def _sub_select(self):
        return super(AccountInvoiceReport, self)._sub_select() + \
               ", SUM ((invoice_type.sign_qty * ail.product_cw_uom_qty) / u.factor * u2.factor) AS product_cw_qty"
