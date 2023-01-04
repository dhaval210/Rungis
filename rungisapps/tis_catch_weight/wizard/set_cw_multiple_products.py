# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SetCwMultipleProducts(models.TransientModel):
    _name = "set.cw.multiple.products"
    _description = "Set Cw Multiple Products"

    catch_weight_ok = fields.Boolean(string="Convert Product", default=False)
    sale_price_base_ok = fields.Boolean(string="Sale Price Based On", default=False)
    purchase_price_base_ok = fields.Boolean(string="Purchase Price Based On", default=False)
    cw_uom_id_ok = fields.Boolean(string="CW Unit Of Measure", default=False)
    catch_weight = fields.Selection([('yes', 'Catch Weight'), ('no', 'Non-Catch Weight')],
                                    string="Convert Prodcut to CW/not")
    sale_price_base = fields.Selection([('uom', 'UOM'), ('cwuom', 'CW-UOM')], string="Sale Price Base")
    purchase_price_base = fields.Selection([('uom', 'UOM'), ('cwuom', 'CW-UOM')], string="Purchase Price Base")

    def _default_cw_uom(self):
        return self.env.ref('uom.product_uom_gram').id

    cw_uom_id = fields.Many2one('uom.uom', string="Catch Weight UOM",
                                default=_default_cw_uom)

    @api.multi
    def create_multiple_cw_products(self):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return
        else:
            active_id = self._context.get('active_ids', [])
            for order in self.env['product.template'].browse(active_id):
                if self.catch_weight_ok == True:
                    if self.catch_weight == "yes":
                        order.write({'catch_weight_ok': True})
                        if self.sale_price_base_ok == True:
                            order.write({'sale_price_base': self.sale_price_base})
                        if self.purchase_price_base_ok == True:
                            order.write({'purchase_price_base': self.purchase_price_base})
                        if self.cw_uom_id_ok == True:
                            order.write({'cw_uom_id': self.cw_uom_id.id})
                    elif self.catch_weight == "no":
                        order.write({'catch_weight_ok': False,
                                     'sale_price_base': 'uom',
                                     'purchase_price_base': 'uom',
                                     'cw_uom_id': False
                                     })

    @api.onchange('sale_price_base_ok', 'cw_uom_id_ok', 'purchase_price_base_ok')
    def onchange_based_on(self):
        self.catch_weight_ok = True

    @api.onchange('catch_weight')
    def onchange_catch_weight(self):
        self.catch_weight_ok = True
