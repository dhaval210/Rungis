# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt Ltd.(<http://technaureus.com/>).


from odoo import fields, http, tools, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):

    @http.route(['/shop/cart/update'], type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        res = super(WebsiteSale, self).cart_update(product_id, add_qty, set_qty, **kw)
        sale_order = request.website.sale_get_order(force_create=True)
        line_id = request.env['sale.order.line'].search(
            [('order_id', '=', sale_order.id), ('product_id', '=', int(product_id))])
        line_id.write({'product_cw_uom_qty': line_id.product_cw_uom_qty + float((kw.get('add_cw_qty', 0))),
                       'product_cw_uom': line_id.product_id.cw_uom_id.id})
        return res
