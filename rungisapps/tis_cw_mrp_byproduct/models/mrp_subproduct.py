# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp


class MrpSubProduct(models.Model):
    _inherit = 'mrp.subproduct'

    cw_product_qty = fields.Float(
        'CW Product Qty',
        digits=dp.get_precision('Product CW Unit of Measure'))
    product_cw_uom_id = fields.Many2one('uom.uom', 'CW Unit of Measure')

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super(MrpSubProduct, self).onchange_product_id()
        if self.product_id:
            self.product_cw_uom_id = self.product_id.cw_uom_id.id
        return res

    @api.onchange('product_cw_uom_id')
    def onchange_cw_uom(self):
        res = {}
        if self.product_cw_uom_id and self.product_id and self.product_cw_uom_id.category_id != self.product_id.cw_uom_id.category_id:
            res['warning'] = {
                'title': _('Warning'),
                'message': _(
                    'The unit of measure you chose is in a different category than the product Catch Weight unit of measure.')
            }
            self.product_cw_uom_id = self.product_id.cw_uom_id.id
        return res
