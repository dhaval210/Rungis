from odoo import api, _
from odoo.exceptions import UserError
from odoo.addons.tis_catch_weight.models.sale import SaleOrder as TisSaleOrder


@api.multi
def action_confirm(self):
    for line in self.order_line:
        if line.product_id._is_cw_product():
            if line.product_cw_uom_qty == 0 and line.product_uom_qty != 0:
                raise UserError(_("Please enter the CW Quantity for %s") % (line.product_id.name))
            elif line.product_cw_uom_qty != 0 and line.product_uom_qty == 0:
                raise UserError(_("Please enter the Quantity for %s") % (line.product_id.name))
    return super(TisSaleOrder, self).action_confirm()


TisSaleOrder.action_confirm = action_confirm
