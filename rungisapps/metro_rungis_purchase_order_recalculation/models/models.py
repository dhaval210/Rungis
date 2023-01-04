# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    recalculated_packaging_unit = fields.Char(string="Packaging Unit")

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        """
        This funtions overwritten to calculated the packaging Units on Purchase Order Lines
        """

        if self.product_id and self.product_qty>0:
            recalculated_packaging_unit = "This equals to "
            prod_qty = self.product_qty or 0
            prod_uom = self.product_uom or False
            packaging_units = {}
            if self.product_id.packaging_ids and  self.product_id.packaging_ids.filtered(lambda x: x.product_uom_id.id== prod_uom.id):
                packaging_ids = self.product_id.packaging_ids.filtered(lambda x: x.product_uom_id.id== prod_uom.id).sorted(lambda s: (-s.qty))
                is_qty_updated = False
                for packaging_id in packaging_ids:
                    remainder = prod_qty % packaging_id.qty
                    if remainder==0 or not remainder==prod_qty:
                        is_qty_updated = True
                        new_packaging_unit = prod_qty//packaging_id.qty
                        prod_qty = prod_qty%packaging_id.qty
                        packaging_units[packaging_id.name] = new_packaging_unit

                        if recalculated_packaging_unit ==  "This equals to ":
                            recalculated_packaging_unit += str(new_packaging_unit) + ' ' +packaging_id.name
                        else:
                            recalculated_packaging_unit +=  ' and ' +str(new_packaging_unit) + ' ' +packaging_id.name
                if is_qty_updated:
                    if prod_qty and prod_qty>0:
                        packaging_units[prod_uom.name] = prod_qty

                        if recalculated_packaging_unit ==  "This equals to ":
                            recalculated_packaging_unit += str(prod_qty) + ' ' + prod_uom.name
                        else:
                            recalculated_packaging_unit += ' and '+str(prod_qty) + ' ' + prod_uom.name
                    
                    self.recalculated_packaging_unit = recalculated_packaging_unit
                else:
                    self.recalculated_packaging_unit = ''
        
        res = super(PurchaseOrderLine, self)._onchange_quantity()
        return res
