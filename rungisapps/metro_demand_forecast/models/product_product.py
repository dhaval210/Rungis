from odoo import models, fields
from odoo.tools import pycompat,float_is_zero
from odoo.tools.float_utils import float_round


class Product(models.Model):
    _inherit = 'product.product'

    def _compute_quantities_dict(self, lot_id, owner_id, package_id, from_date=False, to_date=False):
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations()
        domain_quant = [('product_id', 'in', self.ids)] + domain_quant_loc
        dates_in_the_past = False
        to_date = fields.Datetime.to_datetime(to_date)
        if to_date and to_date < fields.Datetime.now():
            dates_in_the_past = True

        domain_move_in = [('product_id', 'in', self.ids)]
        domain_move_out = [('product_id', 'in', self.ids)]
        if lot_id is not None:
            domain_quant += [('lot_id', '=', lot_id)]
        if owner_id is not None:
            domain_quant += [('owner_id', '=', owner_id)]
            domain_move_in += [('restrict_partner_id', '=', owner_id)]
            domain_move_out += [('restrict_partner_id', '=', owner_id)]
        if package_id is not None:
            domain_quant += [('package_id', '=', package_id)]
        if from_date:
            domain_move_in += [('date_planned', '>=', from_date)]
        else:
            domain_move_in += [('date_planned', '>=', fields.Datetime.to_string(fields.Datetime.now()))]
        if to_date:
            domain_move_in += [('date_planned', '<=', to_date)]

        Move = self.env['stock.move']
        SOrder = self.env['sale.order']
        SLines = self.env['sale.order.line']
        POrder = self.env['purchase.order']
        PLines = self.env['purchase.order.line']
        Quant = self.env['stock.quant']

        if from_date:
            sales = SOrder.search([('commitment_date', '>=', from_date)])
            purchase = POrder.search([('date_planned', '>=', from_date)])
        else:
            sales = SOrder.search([('commitment_date', '>=', fields.Datetime.to_string(fields.Datetime.now()))])
            purchase = POrder.search([('date_planned', '>=', fields.Datetime.to_string(fields.Datetime.now()))])

        domain_move_in_todo = [('order_id', 'in', purchase.ids)] + domain_move_in
        domain_move_out_todo = [('state', 'in', ('draft', 'sent', 'sale')), ('order_id', 'in', sales.ids)] + domain_move_out

        moves_in_res = dict((item['product_id'][0], item['product_qty'] - item['qty_received']) for item in PLines.read_group(domain_move_in_todo, ['product_id', 'product_qty', 'qty_received'], ['product_id'], orderby='id'))
        moves_out_res = dict((item['product_id'][0], item['demand_qty'] - item['qty_delivered'] if item['demand_qty'] > 0 else item['product_uom_qty'] - item['qty_delivered']) for item in SLines.read_group(domain_move_out_todo, ['product_id', 'demand_qty', 'product_uom_qty', 'qty_delivered'], ['product_id'], orderby='id'))

        quants_res = dict((item['product_id'][0], item['quantity']) for item in Quant.read_group(domain_quant, ['product_id', 'quantity'], ['product_id'], orderby='id'))

        res = dict()
        for product in self.with_context(prefetch_fields=False):
            product_id = product.id
            rounding = product.uom_id.rounding
            res[product_id] = {}
            qty_available = quants_res.get(product_id, 0.0)

            res[product_id]['qty_available'] = float_round(qty_available, precision_rounding=rounding)
            res[product_id]['incoming_qty'] = float_round(moves_in_res.get(product_id, 0.0), precision_rounding=rounding)
            res[product_id]['outgoing_qty'] = float_round(moves_out_res.get(product_id, 0.0), precision_rounding=rounding)
            res[product_id]['virtual_available'] = float_round(
                qty_available + res[product_id]['incoming_qty'] - res[product_id]['outgoing_qty'],
                precision_rounding=rounding)

        return res
