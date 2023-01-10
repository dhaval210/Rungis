# -*- coding: utf-8 -*-
#################################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2019-today Ascetic Business Solution <www.asceticbs.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################

from odoo import api,fields,models,_
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Raise the warning "Minimum order quantity of the product <Name> is <Quantity Value>." 
    # if the order quantity is less than the 'Minimum Order Quantity' of the Product.
    @api.one
    @api.constrains('order_line')
    def check_constraint_quantity(self):
        for record in self:
            if record.order_line:
                for product_ids in record.order_line:
                    product = product_ids.product_id.id 
                    minimum_order_qty = self.env['product.product'].browse(product).minimum_order_quantity 
                    if product_ids.product_uom_qty < minimum_order_qty: 
                        raise ValidationError(_('Minimum order quantity of the product' +product_ids.name+' is ' +str(minimum_order_qty)))  
