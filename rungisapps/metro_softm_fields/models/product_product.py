from odoo import models, fields, api


class MetroExtend_ProductProduct(models.Model):
    _inherit = 'product.product'

    categ_main_id = fields.Char(string="categ_main_id")
    softm_location_number = fields.Integer('SoftM Lagernummer')

    @api.multi
    def write(self, values):
        if (
            len(self) == 1 and
            'uom_id' in values and
            self.uom_id.id == values['uom_id']
        ):
            del values['uom_id']
        # Make sure to determin if active is different before writing to database
        # this will prevent recursion in the if-clause, since the template also tries to archive it's variants
        active_changed = False
        if "active" in values:
            active_changed = values["active"] != self.active
        res = super().write(values)
        # Make sure to deactivate reordering rules and archive the template
        if ("active" in values and active_changed):
            if values["active"] == False:
                self.mapped('orderpoint_ids').filtered(lambda r: r.active).write({'active': False})
            self.product_tmpl_id.write({'active': values["active"]})
        return res
