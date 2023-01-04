# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import tools
from odoo import api, fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"
    _auto = False

    cw_qty_delivered = fields.Float('CW Qty Delivered', readonly=True)
    cw_qty_invoiced = fields.Float('CW Qty Invoiced', readonly=True)
    product_cw_uom_qty = fields.Float('CW Qty Ordered', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['product_cw_uom_qty'] = ", sum(l.product_cw_uom_qty / u.factor * u2.factor) as product_cw_uom_qty"
        fields['cw_qty_delivered'] = ", sum(l.cw_qty_delivered / u.factor * u2.factor) as cw_qty_delivered"
        fields['cw_qty_invoiced'] = ", sum(l.cw_qty_invoiced / u.factor * u2.factor) as cw_qty_invoiced"
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
