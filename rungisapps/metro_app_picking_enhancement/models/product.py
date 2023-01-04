from odoo import models, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def check_deviation_warning_js(self, cw_qty, qty, uom, cw_uom):
        cw_uom = self.env['uom.uom'].browse(cw_uom)
        uom = self.env['uom.uom'].browse(uom)
        cw_uom_qty = cw_uom._compute_quantity(cw_qty, self.cw_uom_id)
        uom_qty = uom._compute_quantity(qty, self.uom_id)
        if self.average_cw_quantity:
            deviation = self.average_cw_quantity * (self.max_deviation / 100)
            deviation_max_value = self.average_cw_quantity + deviation
            deviation_min_value = abs(self.average_cw_quantity - deviation)
            if (cw_uom_qty / uom_qty) < deviation_max_value:
                deviation_value = abs((cw_uom_qty / uom_qty) - deviation_max_value)
            else:
                deviation_value = abs((cw_uom_qty / uom_qty) - deviation_min_value)
            if (cw_uom_qty / uom_qty) < deviation_min_value or (cw_uom_qty / uom_qty) > deviation_max_value:
                warning_mess = {
                    'title': _('Exceeds Maximum Deviation!'),
                    'message': _('\nAverage CW quantity Deviated From Expected Deviation.')
                }
                return warning_mess
        return {}
