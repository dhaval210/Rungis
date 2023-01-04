# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Avinash Nk(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import datetime, date
from odoo import models, api, fields, _
from odoo.exceptions import UserError


class ExpiryDateWarning(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        super(ExpiryDateWarning, self).product_uom_change()
        if self.product_id:
            total_quantity = 0.0
            product_sale = self.product_id
            quantity_in_lot = self.env['stock.quant'].search([('product_id','=',product_sale.id),('location_id','=', self.order_id.warehouse_id.pick_type_id.default_location_src_id.id)])
            lot_number_obj = self.env['stock.production.lot']
            lot_number_obj_specific = lot_number_obj.search([('product_id','=',product_sale.id)])
            for records in lot_number_obj_specific:
                dates = date.today()
                if records.use_date:
                    dates = records.use_date.date()
                if records.product_id.id == product_sale.id and dates < date.today():
                    for values in quantity_in_lot:
                        if values.lot_id.id == records.id and values.product_id.id == product_sale.id:
                            total_quantity = total_quantity+values.quantity
            total_quantity = sum([quant['quantity'] for quant in quantity_in_lot])
            good_products = self.product_id.qty_available - total_quantity
            if good_products < self.product_uom_qty:
                warning_mess = {
                    'title': _('Not enough good products!'),
                    'message': _(
                        'You plan to sell %.2f %s but you only have %.2f %s Good Products available!\n'
                        'The stock on hand is %.2f %s.') % (
                            self.product_uom_qty, self.product_uom.name, good_products,
                            self.product_id.uom_id.name,
                            self.product_id.qty_available, self.product_id.uom_id.name)
                }
                return {'warning': warning_mess}


#following code issues a blocking warning if a transfer is created with expired products. This logic has to be narrowed down so
# 1. it is possible to create internal transfers with expired products to book them out of stock
# 2. The module metro_expired_transfer can work
# --> Workshop necessary to decide what to do (for example restrict on picking type if checkbox "Don't allow expired product transfers")


#class StockMove(models.Model):
#    _inherit = "stock.move"

#    @api.multi
#    def write(self, vals):
#        lots = [x.lot_id for x in self.move_line_ids]
#        lot_list = []
#        for lot in lots:
#            if self.product_id == lot.product_id:
#                if lot.use_date:
#                    use_date = datetime.strptime(str(lot.use_date), '%Y-%m-%d %H:%M:%S').date()
#                    if use_date < date.today():
#                        lot_list.append(str(lot.name))
#        if len(lot_list) == 1:
#            raise UserError(_('Product in this lot number is expired : %s' % lot_list[0]))
#        elif len(lot_list) > 1:
#            raise UserError(_('Products in these lot numbers are expired : %s' % lot_list))
#        res = super(StockMove, self).write(vals)
#        return res
