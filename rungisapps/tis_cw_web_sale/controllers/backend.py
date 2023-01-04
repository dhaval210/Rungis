# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt Ltd.(<http://technaureus.com/>).

from odoo import fields, http, _
from odoo.addons.website.controllers.backend import WebsiteBackend
from odoo.http import request


class WebsiteSaleBackend(WebsiteBackend):

    @http.route()
    def fetch_dashboard_data(self, website_id, date_from, date_to):
        Website = request.env['website']
        current_website = website_id and Website.browse(website_id) or Website.get_current_website()

        results = super(WebsiteSaleBackend, self).fetch_dashboard_data(website_id, date_from, date_to)
        # add cw qty to best seller's table
        report_product_lines = request.env['sale.report'].read_group(
            domain=[
                ('website_id', '=', current_website.id),
                ('team_id.team_type', '=', 'website'),
                ('state', 'in', ['sale', 'done']),
                ('confirmation_date', '>=', date_from),
                ('confirmation_date', '<=', fields.Datetime.now())],
            fields=['product_cw_uom_qty'],
            groupby='product_tmpl_id', orderby='product_uom_qty desc', limit=5)
        for product_line in report_product_lines:
            results['dashboards']['sales']['best_sellers'][0].update({
                'cw_qty': product_line['product_cw_uom_qty'],
            })
        return results
