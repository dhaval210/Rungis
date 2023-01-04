
from odoo import api, models, _, tools
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.multi
    def button_approve(self, force=False):
        res = super().button_approve(force)
        for rec in self:
            for line in rec.order_line:
                line.product_id.set_product_last_purchase(line.company_id.id)
        return res

    @api.multi
    def button_cancel(self):
        res = super().button_cancel()
        for rec in self:
            for line in rec.order_line:
                line.product_id.set_product_last_purchase(line.company_id.id)
        return res


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def write(self, vals):
        result = super().write(vals)
        for line in self:
            if line.order_id.id is not False and line.order_id.state == 'purchase':
                line.product_id.set_product_last_purchase(line.company_id.id)
        return result


class UomUom(models.Model):
    _inherit = 'uom.uom'

    @api.multi
    def _compute_lpp_quantity(self, qty, to_unit, round=True, rounding_method='UP', raise_if_failure=True):
        if not self or not qty:
            return qty
        self.ensure_one()

        if self != to_unit and self.category_id.id != to_unit.category_id.id:
            if raise_if_failure:
                raise UserError(
                    _('The unit of measure %s defined on the order line doesn\'t belong to the same category than the unit of measure %s defined on the product. Please correct the unit of measure defined on the order line or on the product, they should belong to the same category.') % (
                    self.name, to_unit.name))
            else:
                return qty

        if self == to_unit:
            amount = qty
        else:
            amount = qty / self.factor
            if to_unit:
                amount = amount * to_unit.factor

        return amount

