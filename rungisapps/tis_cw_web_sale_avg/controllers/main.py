# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt Ltd.(<http://technaureus.com/>).

from odoo import fields, http, tools, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleInherit(WebsiteSale):

    @http.route(['/shop/cart/update_json_cw'], type='json', auth="public", methods=['POST'], website=True,
                   csrf=False)
    def cart_update_json_cw(self, product_id, line_id=None, set_qty=None):
        line = False
        if line_id:
            line = request.env['sale.order.line'].browse([line_id])
        if line:
            set_qty = set_qty and float(set_qty)
            line.write({'product_cw_uom_qty': set_qty})

    @http.route(['/shop/cart/check_has_uom_field'], type='json', auth="public", methods=['POST'], website=True,
                   csrf=False)
    def check_average_uom_qty(self, product_id=False):
        Template = False
        if product_id:
            Template = request.env['product.product'].browse([product_id]).product_tmpl_id
        if Template:
            return Template.get_cw_qty()
