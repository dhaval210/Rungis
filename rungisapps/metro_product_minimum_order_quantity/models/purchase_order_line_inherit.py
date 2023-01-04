from odoo import models, api, _

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    @api.constrains('product_qty', 'product_id')
    def _check_product_qty(self):
        for line in self:
            seller_min_qty = self.product_id.seller_ids \
                .filtered(lambda r: r.name == self.order_id.partner_id) \
                .sorted(key=lambda r: r.min_qty)

        if seller_min_qty.min_qty > line.product_qty:
            return False
        else:
            return True

#    _constraints = [
#        (_check_product_qty, 'Ordered Quantity is below MOQ.!', ['product_qty'])
#    ]

    @api.onchange('product_qty')
    def _onchange_product_qty(self):
#        res = super(PurchaseOrderLine, self)._onchange_quantity()
        seller_min_qty = self.product_id.seller_ids \
            .filtered(lambda r: r.name == self.order_id.partner_id) \
            .sorted(key=lambda r: r.min_qty)
        if seller_min_qty.min_qty > self.product_qty:
            warning_mess = {
                'title': _('Ordered quantity decreased!'),
                'message': _('Ordered Quantity is below MOQ.!'),
            }
            return {'warning': warning_mess}
#        return res









